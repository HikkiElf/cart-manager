from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

DB_HOST = "localhost"
DB_NAME = "Market"
DB_USER = "postgres"
DB_PASSWD = os.environ.get("DB_PASSWD")

async def get_db():
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWD)
        yield conn
    finally:
        if conn:
            conn.close()
            

class CartItem(BaseModel):
    user_id: int
    product_id: int
    quantity: int

class CartItemDelete(BaseModel): 
    user_id: int
    product_id: int
    

async def init_db(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        """)
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error initializing database: {e}")
        

@app.on_event("startup")
async def startup_event():
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWD)
        await init_db(conn)
    finally:
        if conn:
            conn.close()

            
@app.post("/cart/")
async def add_to_cart(item: CartItem, conn = Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
            (item.user_id, item.product_id, item.quantity),
        )
        conn.commit()
        return {"message": "Item added to cart"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.put("/cart/")
async def update_cart(item: CartItem, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
            (item.quantity, item.user_id, item.product_id),
        )
        conn.commit()
        if cur.rowcount == 0:
             raise HTTPException(status_code=404, detail="Item not found in cart")
        return {"message": "Cart updated"}
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.delete("/cart/")
async def delete_from_cart(item: CartItemDelete, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM cart WHERE user_id = %s AND product_id = %s",
            (item.user_id, item.product_id),
        )
        conn.commit()
        if cur.rowcount == 0:
             raise HTTPException(status_code=404, detail="Item not found in cart")
        return {"message": "Item removed from cart"}

    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

