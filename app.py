import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# --- Lavender theme CSS ---
def set_lavender_theme():
    st.markdown(
        """
        <style>
        /* Background */
        .main {
            background-color: #f3eafa;
        }
        /* Sidebar */
        .css-1d391kg {
            background-color: #e0d6f8;
        }
        /* Headers */
        .css-1v0mbdj h1, .css-1v0mbdj h2, .css-1v0mbdj h3 {
            color: #967bb6;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        /* Buttons */
        button[kind="primary"] {
            background-color: #967bb6 !important;
            color: white !important;
        }
        /* Tables */
        .css-1lcbmhc {
            background-color: #e9dff4 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# --- Database helpers ---
def get_connection():
    return sqlite3.connect('sales_inventory.db')

def add_product(name, price, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)", (name, price, quantity))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_product_quantity(product_id, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET quantity = quantity + ? WHERE product_id = ?", (quantity, product_id))
    conn.commit()
    conn.close()

def record_sale(product_id, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
    stock = cursor.fetchone()[0]
    if stock < quantity:
        conn.close()
        return False
    cursor.execute("UPDATE products SET quantity = quantity - ? WHERE product_id = ?", (quantity, product_id))
    cursor.execute("INSERT INTO sales (product_id, quantity, sale_date) VALUES (?, ?, ?)",
                   (product_id, quantity, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return True

def get_products():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()
    return df

def get_sales():
    conn = get_connection()
    df = pd.read_sql(
        "SELECT s.sale_id, p.name AS product_name, s.quantity, s.sale_date FROM sales s JOIN products p ON s.product_id = p.product_id",
        conn)
    conn.close()
    return df

# --- Streamlit app ---
def main():
    set_lavender_theme()
    st.title("Sales & Inventory Management System")

    menu = ["Add Product", "Update Stock", "Record Sale", "View Inventory", "View Sales", "Dashboard"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add Product":
        st.subheader("Add New Product")
        name = st.text_input("Product Name")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        quantity = st.number_input("Initial Quantity", min_value=0, step=1)

        if st.button("Add Product"):
            if not name.strip():
                st.error("Please enter a product name.")
            elif add_product(name.strip(), price, quantity):
                st.success(f"Product '{name}' added successfully!")
            else:
                st.error(f"Product '{name}' already exists.")

    elif choice == "Update Stock":
        st.subheader("Update Stock Quantity")
        products = get_products()
        if products.empty:
            st.info("No products found. Please add products first.")
            return
        product_dict = dict(zip(products['name'], products['product_id']))
        selected_product = st.selectbox("Select Product", list(product_dict.keys()))
        add_qty = st.number_input("Add Quantity", min_value=1, step=1)

        if st.button("Update Stock"):
            update_product_quantity(product_dict[selected_product], add_qty)
            st.success(f"Stock updated for {selected_product}!")

    elif choice == "Record Sale":
        st.subheader("Record a Sale")
        products = get_products()
        if products.empty:
            st.info("No products found. Please add products first.")
            return
        product_dict = dict(zip(products['name'], products['product_id']))
        selected_product = st.selectbox("Select Product", list(product_dict.keys()))
        sale_qty = st.number_input("Quantity Sold", min_value=1, step=1)

        if st.button("Record Sale"):
            if record_sale(product_dict[selected_product], sale_qty):
                st.success("Sale recorded successfully!")
            else:
                st.error("Not enough stock!")

    elif choice == "View Inventory":
        st.subheader("Current Inventory")
        products = get_products()
        st.dataframe(products)

    elif choice == "View Sales":
        st.subheader("Sales Records")
        sales = get_sales()
        st.dataframe(sales)

    elif choice == "Dashboard":
        st.subheader("Sales and Inventory Dashboard")
        products = get_products()
        sales = get_sales()

        # Inventory bar chart
        st.markdown("### Inventory Stock Levels")
        fig, ax = plt.subplots()
        ax.bar(products['name'], products['quantity'], color='#967bb6')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        # Sales over time
        st.markdown("### Sales Over Time")
        if sales.empty:
            st.info("No sales records to display.")
        else:
            sales['sale_date'] = pd.to_datetime(sales['sale_date'])
            sales_over_time = sales.groupby('sale_date')['quantity'].sum()
            fig2, ax2 = plt.subplots()
            ax2.plot(sales_over_time.index, sales_over_time.values, marker='o', color='#967bb6')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)

if __name__ == '__main__':
    main()
