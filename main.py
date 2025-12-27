import uvicorn
#from app.app import app


#server

if __name__ == "__main__":
    uvicorn.run("app.app:app",host="0.0.0.0",port=8000,reload=True)