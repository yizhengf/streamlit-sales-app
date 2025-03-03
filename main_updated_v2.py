import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def read_file(file):
    try:
        df = pd.read_csv(file, sep='\t')
        if len(df.columns) == 1:
            file.seek(0)
            df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error reading file {file.name}: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Product Sales Analysis", layout="wide")
    st.title('Product Sales & Net Income Analysis')

    uploaded_files = st.sidebar.file_uploader(
        "Upload TSV/CSV files", type=['txt', 'tsv', 'csv'], accept_multiple_files=True
    )

    if not uploaded_files:
        st.info('👆 Please upload TSV or CSV files')
        return

    df_list = [read_file(file) for file in uploaded_files if read_file(file) is not None]

    if not df_list:
        st.error("No valid files were uploaded")
        return

    df = pd.concat(df_list, ignore_index=True)

    # 转换数据类型
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df['item-price'] = pd.to_numeric(df['item-price'], errors='coerce')
    df['refund-amount'] = pd.to_numeric(df['refund-amount'], errors='coerce').fillna(0)

    # 计算销售额和净收入
    df['product_sales'] = df['quantity'] * df['item-price']
    df['total'] = df['product_sales'] - df['refund-amount']

    # 按 SKU 计算累计销售额和净收入
    sku_sales_summary = df.groupby('sku').agg({
        'product_sales': 'sum',
        'total': 'sum'
    }).sort_values(by='product_sales', ascending=False)

    # 显示数据表
    st.subheader("SKU Sales Summary")
    st.dataframe(sku_sales_summary)

    # 可视化：销售额
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    sku_sales_summary['product_sales'].plot(kind='bar', ax=ax1, color='royalblue')
    ax1.set_title("Total Product Sales by SKU")
    ax1.set_xlabel("SKU")
    ax1.set_ylabel("Total Sales ($)")
    ax1.tick_params(axis='x', rotation=45)
    st.pyplot(fig1)

    # 可视化：净收入
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    sku_sales_summary['total'].plot(kind='bar', ax=ax2, color='green')
    ax2.set_title("Total Net Income by SKU")
    ax2.set_xlabel("SKU")
    ax2.set_ylabel("Net Income ($)")
    ax2.tick_params(axis='x', rotation=45)
    st.pyplot(fig2)

    # 统计总数据
    total_sales = sku_sales_summary['product_sales'].sum()
    net_income = sku_sales_summary['total'].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Product Sales", f"${total_sales:,.2f}")
    with col2:
        st.metric("Total Net Income", f"${net_income:,.2f}")

if __name__ == "__main__":
    main()
