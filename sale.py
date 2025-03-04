import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import re
from datetime import datetime

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
            hour_match = re.search(r'(\d{1,2}):\d{2}:\d{2} (AM|PM)', date_str)
            if year_match and hour_match:
                year = year_match.group(1)
                hour = int(hour_match.group(1))
                if hour_match.group(2) == 'PM' and hour != 12:
                    hour += 12  # PM且不是12点，转换为24小时制
                elif hour_match.group(2) == 'AM' and hour == 12:
                    hour = 0  # AM且是12点，转换为0点
                return year, month_num, date_str, hour  # 返回原始日期字符串和小时
            else:
                return None, month_num, date_str, None
            
    return None, None, date_str, None

def process_data(df):
    """
    处理数据，确保数据类型正确并计算销售额
    """
    # 确保 quantity 列为数值类型
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')  # 将无法转换的值设置为 NaN

    # 确保 product-sales 列为数值类型
    df['product-sales'] = pd.to_numeric(df['product-sales'], errors='coerce')  # 将无法转换的值设置为 NaN

    # 检查是否有 NaN 值
    if df['quantity'].isnull().any() or df['product-sales'].isnull().any():
        st.warning("Warning: Some rows contain NaN values in 'quantity' or 'product-sales'. These rows will be dropped.")

    # 删除包含 NaN 的行
    df = df.dropna(subset=['quantity', 'product-sales'])

    # 计算销售额
    df['sales_amount'] = df['quantity'] * df['product-sales']  # 计算销售额
    st.write(df.head())

    # 检查 sales_amount 列是否成功创建
    if 'sales_amount' not in df.columns:
        st.error("Sales amount calculation failed. Please check your data.")
        st.write(df.head())  # 输出 DataFrame 的前几行以便调试
        return df  # 返回未修改的 DataFrame
    return df

def parse_purchase_date(date_str):
    """
    解析 purchase-date 字符串，返回日期和小时
    """
    try:
        # 解析格式为 'Jan 16, 2024 8:35:49 AM PST'
        date_obj = datetime.strptime(date_str, '%b %d, %Y %I:%M:%S %p %Z')
        return date_obj.date(), date_obj.hour  # 返回日期和小时
    except ValueError:
        return None, None  # 如果日期格式不正确，返回 None


def extract_year_month(df):
    """
    从 purchase-date 列中提取年份和月份
    """
    years = []
    months = []
    for date_str in df['purchase-date']:
        date_obj = parse_purchase_date(date_str)
        if date_obj:
            years.append(date_obj.year)
            months.append(date_obj.month)
        else:
            years.append(None)
            months.append(None)
    return years, months

def main():
    st.set_page_config(page_title="product-sales Analysis", layout="wide")
    st.title('product-sales Analysis')
    
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
        # 提取日期和小时信息
        df['purchase-date'] = df['purchase-date'].astype(str)  # 确保为字符串格式
        df['date'], df['hour'] = zip(*df['purchase-date'].apply(parse_purchase_date))  # 提取日期和小时

        # 处理数据并计算销售额
        df = process_data(df)

        # 检查 sales_amount 列是否存在
        if 'sales_amount' not in df.columns:
            st.error("Sales amount calculation failed. Please check your data.")
            return

        # 确保 quantity 列为数值类型
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

        date_column = 'date/time' if 'date/time' in df.columns else 'purchase-date'
        
        # 处理日期，使用手动解析
        years = []
        months = []
        days = []
        hours= []
        
        for date_str in df[date_column].astype(str):
            year, month, original_date, hour = parse_date(date_str)
            years.append(year)
            months.append(month)
            days.append(original_date)  # 直接使用原始日期字符串
            hours.append(hour)

        df['year'] = years
        df['month_only'] = months
        df['date'] = days  # 保留原始日期字符串
        df['hour_only'] = hours # 保留小时

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
            index= 0 if filtered_product_names else -1  # 不设默认值
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
            default=["Order"]  # 默认选择 "Order"
        )
        
        # 使用滑动条选择展示销量前 N 的 SKU
        top_n = st.sidebar.slider(
            "Select Top N SKUs to Display",
            min_value=1,
            max_value= len(df['sku'].unique()),  # 假设最多展示 20 个 SKU
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
        # 绘制月度热图
        plt.figure(figsize=(12, 6))
        sns.heatmap(pivot_sales, cmap='YlGnBu', annot=True, fmt='g', linewidths=.5)
        plt.title(f'Monthly Sales Heatmap by SKU (Top {top_n})')
        plt.xlabel('SKU')
        plt.ylabel('Month')
        st.pyplot(plt)
         
        # 统计每个 SKU 的每个小时的销量
        hourly_sales = df_filtered.groupby(['year', 'hour_only', 'sku']).agg(
            total_sales=('quantity', 'sum')
        ).reset_index()

        # 获取销量前 N 的 SKU
        top_skus = hourly_sales.groupby('sku')['total_sales'].sum().nlargest(top_n).index
        hourly_sales_top = hourly_sales[hourly_sales['sku'].isin(top_skus)]

        # 创建透视表以便于绘图
        pivot_sales_hour = hourly_sales_top.pivot_table(
            index='hour_only',  # Y 轴只展示月份
            columns='sku',
            values='total_sales',
            fill_value=0
        )
        # 绘制小时热图
        plt.figure(figsize=(12, 6))
        sns.heatmap(pivot_sales_hour, cmap='YlGnBu', annot=True, fmt='g', linewidths=.5)
        plt.title(f'Hourly Sales Heatmap by SKU (Top {top_n})')
        plt.xlabel('SKU')
        plt.ylabel('Hour')
        st.pyplot(plt)

        #    # 创建透视表以便于绘图
        # pivot_sales = hourly_sales_top.pivot_table(
        #     index='month_only',  # Y 轴只展示月份
        #     columns='sku',
        #     values='total_sales',
        #     fill_value=0
        # )

       
        # # 创建原始透视表以便于绘图，统计每种类型的销量
        # heatmap_data = df_filtered.pivot_table(
        #     index='hour_only',  # Y 轴展示月份
        #     columns='sku',  # X 轴展示 SKU
        #     values='quantity',  # 数量
        #     aggfunc='sum',  # 聚合函数，统计每种类型的销量
        #     fill_value=0  # 填充缺失值为 0
        # )
        #  # 创建透视表，按小时和 SKU 聚合
        # hourly_sales = df.groupby(['hour', 'sku']).agg(
        #     total_sales=('quantity', 'sum')
        # ).reset_index()

       
        # # 绘制小时级别的热力图
        # if not hourly_sales.empty:  # 检查数据是否为空
        #     heatmap_data = hourly_sales.pivot(index='hour', columns='sku', values='total_sales')
        #     plt.figure(figsize=(12, 6))
        #     sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap='YlGnBu')
        #     plt.title(f'Hourly Sales Heatmap')
        #     plt.xlabel('SKU')
        #     plt.ylabel('Hour of the Day')
        #     st.pyplot(plt)
        # else:
        #     st.warning("No data available for the selected date.")

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        raise e

        # 其他图像展示（如小时销售额的热图）
        if not hourly_sales.empty:  # 检查数据是否为空
            plt.figure(figsize=(12, 6))
            sns.heatmap(hourly_sales.pivot(index='hour', columns='total_sales', values='total_quantity'), annot=True, fmt=".1f", cmap='YlGnBu')
            plt.title(f'Hourly Sales Heatmap ')
            plt.xlabel('Total Sales')
            plt.ylabel('Hour of the Day')
            st.pyplot(plt)
        else:
            st.warning("No data available for the selected date.")

        # 统计每种 type 的订单数量和销售额
        order_counts = df_filtered.groupby(['sku', 'type']).agg(
            order_count=('quantity', 'sum'),  # 统计每种类型的订单数量
            total_sales=('quantity', 'sum')  # 统计每种类型的销售额
        ).reset_index()

        # 计算净销售量
        net_sales = df_filtered.groupby('sku').agg(
            net_sales=('quantity', lambda x: x[df_filtered['type'] == 'Order'].sum() - x[df_filtered['type'] == 'Refund'].sum())
        ).reset_index()

        # 合并订单数量、销售额和净销售量
        order_counts = order_counts.merge(net_sales, on='sku', how='left')

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
    
        # 创建原始透视表以便于绘图，统计每种类型的销量
        heatmap_data = df_filtered.pivot_table(
            index='month_only',  # Y 轴展示月份
            columns='sku',  # X 轴展示 SKU
            values='quantity',  # 数量
            aggfunc='sum',  # 聚合函数，统计每种类型的销量
            fill_value=0  # 填充缺失值为 0
        )

        # 仅在同时选择 Order 和 Refund 时创建新的透视表计算净销售量
        if "Order" in selected_types and "Refund" in selected_types:
            net_sales_data = df_filtered.pivot_table(
                index='month_only',
                columns='sku',
                values='quantity',
                aggfunc=lambda x: x[df_filtered['type'] == 'Order'].sum() - x[df_filtered['type'] == 'Refund'].sum(),
                fill_value=0
            )

            # 过滤净销售量数据以匹配用户选择的 SKU
            net_sales_data = net_sales_data.loc[:, net_sales_data.columns.isin(selected_skus)]

            # 确保只保留用户选择的 SKU
            if not net_sales_data.empty:
                # 绘制净销售量热力图
                plt.figure(figsize=(12, 6))
                sns.heatmap(net_sales_data, annot=True, fmt='.2f', cmap='YlGnBu', cbar_kws={'label': 'Net Sales'})
                plt.title('Net Sales by Month and SKU')
                plt.xlabel('SKU')
                plt.ylabel('Month')
                plt.xticks(rotation=45)
                st.pyplot(plt)
        else:
            st.warning('Please select both Order and Refund to display the net sales heatmap.')
   

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        raise e

if __name__ == "__main__":
    main()