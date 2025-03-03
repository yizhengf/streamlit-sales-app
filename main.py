import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import re

def read_file(file):
    """
    @param {file} file - 上传的文件对象
    @return {DataFrame} - 读取的数据框
    """
    try:
        df = pd.read_csv(file, sep='\t')
        if len(df.columns) == 1:
            file.seek(0)
            df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error reading file {file.name}: {str(e)}")
        return None

def parse_date(date_str):
    """
    解析日期字符串，返回年份、月份和日期
    """
    if not date_str:  # 检查是否为空
        return None, None, None

    month_abbr = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    for abbr, month_num in month_abbr.items():
        if abbr in date_str:
            year_match = re.search(r'\b(\d{4})\b', date_str)
            if year_match:
                year = year_match.group(1)
                return year, month_num, date_str  # 返回原始日期字符串
            else:
                return None, month_num, date_str
            
    return None, None, date_str

def main():
    st.set_page_config(page_title="Product Sales Analysis", layout="wide")
    st.title('Product Sales Analysis')
    
    try:
        uploaded_files = st.sidebar.file_uploader(
            "Upload TSV/CSV files", 
            type=['txt', 'tsv', 'csv'],
            accept_multiple_files=True
        )
        
        if not uploaded_files:
            st.info('👆 Please upload TSV or CSV files')
            return
            
        df_list = []
        for file in uploaded_files:
            df = read_file(file)
            if df is not None:
                df_list.append(df)
        
        if not df_list:
            st.error("No valid files were uploaded")
            return
            
        # 合并所有上传的文件数据
        df = pd.concat(df_list, ignore_index=True)

        # 确保 quantity 列为数值类型
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

        date_column = 'date/time' if 'date/time' in df.columns else 'purchase-date'
        
        # 处理日期，使用手动解析
        years = []
        months = []
        days = []
        
        for date_str in df[date_column].astype(str):
            year, month, original_date = parse_date(date_str)
            years.append(year)
            months.append(month)
            days.append(original_date)  # 直接使用原始日期字符串

        df['year'] = years
        df['month_only'] = months
        df['date'] = days  # 保留原始日期字符串

        # 检查是否有未解析的日期
        if None in df['year'] or None in df['month_only']:
            st.warning("Some dates could not be parsed. Please check the date format in your files.")
        
        # 检查 SKU 格式
        df['sku'] = df['sku'].astype(str).str.strip()
        df['sku'] = df['sku'].apply(lambda x: 'S-' + x if x[0].isdigit() else x)

        # 处理 product-name 列，若以数字开头则根据 store 列的值进行处理
        def process_product_name(row):
            if row['product-name'] and row['product-name'][0].isdigit():
                return f"{row['store']}-{row['product-name']}"
            return row['product-name']

        df['product-name'] = df.apply(process_product_name, axis=1)

        # 确保 quantity 列为数值类型
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

        # 将 type 列中的所有数据转换为字符串类型
        df['type'] = df['type'].astype(str)

        st.sidebar.header('Filter Options')
        
        # 年份下拉选择
        available_years = sorted(df['year'].unique())
        selected_years = st.sidebar.selectbox(
            "Select Year",
            options=available_years,
            index=0  # 默认选择第一个年份
        )
        
        # SKU 下拉选择
        available_skus = sorted(df['sku'].unique())
        selected_skus = st.sidebar.multiselect(
            "Select SKUs to Analyze",
            options=available_skus,
            default=available_skus[:5]  # 默认选择前 5 个 SKU
        )
        
        # 月份筛选
        available_months = sorted(df['month_only'].unique())
        selected_months = st.sidebar.multiselect(
            "Select Months",
            options=available_months,
            default=available_months  # 默认选择所有月份
        )
        
        # 产品名称搜索框，包含下拉选项
        product_name_search = st.sidebar.text_input(
            "Search Product Name",
            help="Enter product name to filter"
        ).strip().lower()
        
        # 根据输入的产品名称动态更新下拉选项
        available_product_names = sorted(df['product-name'].unique())
        filtered_product_names = [name for name in available_product_names if product_name_search in name.lower()]
        selected_product_name = st.sidebar.selectbox(
            "Select Product Name",
            options=filtered_product_names,
            index=0 if filtered_product_names else -1  # 不设默认值
        )
        
        # 单独的 SKU 搜索框
        sku_search = st.sidebar.text_input(
            "Search SKU",
            help="Enter SKU to filter"
        ).strip().lower()
        
        # type 列筛选，使用提供的选项
        available_types = [
            "(Blanks)", "A-to-z Guarantee Claim", "Adjustment", "Chargeback Refund",
            "FBA Customer Return Fee", "FBA Inventory Fee", "FBA Transaction fees",
            "Liquidations", "Liquidations Adjustments", "Order", "Order_Retrocharge",
            "Refund", "Refund_Retrocharge", "Service Fee", "Shipping Services", "Transfer"
        ]
        selected_types = st.sidebar.multiselect(
            "Select Types",
            options=available_types,
            default=["Order", "Refund"]  # 默认选择 "Order" 和 "Refund"
        )
        
        # 使用滑动条选择展示销量前 N 的 SKU
        top_n = st.sidebar.slider(
            "Select Top N SKUs to Display",
            min_value=1,
            max_value=20,  # 假设最多展示 20 个 SKU
            value=5  # 默认选择前 5 个 SKU
        )
        
        # 过滤数据
        df_filtered = df[
            (df['sku'].isin(selected_skus) | df['sku'].str.contains(sku_search, case=False, na=False)) &
            (df['month_only'].isin(selected_months)) &
            (df['year'] == selected_years) &
            (df['type'].isin(selected_types))  # 根据选择的类型进行筛选
        ]
        
        # 移除 SKU 为 NaN 的行
        df_filtered = df_filtered[df_filtered['sku'].notna()]
        
        # 调试信息：打印筛选前后的数据
        st.write("Original DataFrame shape:", df.shape)
        st.write("Filtered DataFrame shape:", df_filtered.shape)

        if df_filtered.empty:
            st.warning('No data matches your filter criteria')
            return
        
       
        # 统计每个 SKU 的每个月的销量
        monthly_sales = df_filtered.groupby(['year', 'month_only', 'sku']).agg(
            total_sales=('quantity', 'sum')
        ).reset_index()

        # 获取销量前 N 的 SKU
        top_skus = monthly_sales.groupby('sku')['total_sales'].sum().nlargest(top_n).index
        monthly_sales_top = monthly_sales[monthly_sales['sku'].isin(top_skus)]




       # 创建透视表以便于绘图
        pivot_sales = monthly_sales_top.pivot_table(
            index='month_only',  # Y 轴只展示月份
            columns='sku',
            values='total_sales',
            fill_value=0
        )
      # 绘制热图
        plt.figure(figsize=(12, 6))
        sns.heatmap(pivot_sales, cmap='YlGnBu', annot=True, fmt='g', linewidths=.5)
        plt.title(f'Monthly Sales Heatmap by SKU (Top {top_n})')
        plt.xlabel('SKU')
        plt.ylabel('Month')
        st.pyplot(plt)

        # 统计每种 type 的订单数量
        order_counts = df_filtered.groupby(['sku', 'type']).size().reset_index(name='order_count')

        # 获取销量前 N 的 SKU
        top_skus = order_counts.groupby('sku')['order_count'].sum().nlargest(top_n).index
        order_counts_top = order_counts[order_counts['sku'].isin(top_skus)]

        # 绘制柱状图，使用不同颜色区分不同类型
        plt.figure(figsize=(12, 6))
        palette = sns.color_palette("husl", len(selected_types))  # 使用不同颜色
        for i, t in enumerate(selected_types):
            subset = order_counts_top[order_counts_top['type'] == t]
            bars = plt.bar(subset['sku'], subset['order_count'], color=palette[i], label=t)

            # 在每个柱子上添加数量标签
            for bar in bars:
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), round(bar.get_height(), 2), ha='center', va='bottom')

        # 在标题中区分不同类型
        plt.title(f'Total Orders by SKU (Top {top_n}) - Types: {", ".join(selected_types)}')
        plt.xlabel('SKU')
        plt.ylabel('Order Count')
        plt.xticks(rotation=45)
        plt.legend(title='Type')

        st.pyplot(plt)

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        raise e

if __name__ == "__main__":
    main()