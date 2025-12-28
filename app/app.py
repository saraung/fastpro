from fastapi import FastAPI,HTTPException,File,UploadFile,Form,Depends
from app.schemas import PostCreate,PostResponse
from app.db import Post,create_db_and_tables,get_async_session,User
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.images import imagekit
import shutil
import os
import uuid
import tempfile
from app.users import current_active_user,auth_backend,fastapi_users
from app.schemas import UserRead,UserCreate,UserUpdate
@asynccontextmanager
async def lifespan(app:FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend),prefix="/auth/jwt",tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead,UserCreate),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead),prefix="/auth",tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead,UserUpdate),prefix="/users",tags=["users"])
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user: User= Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    temp_file_path = None

    try:
        # Save to temp file (optional but fine)
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        # ✅ NEW SDK upload
        with open(temp_file_path, "rb") as f:
            response = imagekit.files.upload(
                file=f,
                file_name=file.filename,
                folder="/backend-uploads",
                tags=["backend-upload"],
                use_unique_file_name=True,
            )

        # Defensive check
        if not response or not response.url:
            raise HTTPException(status_code=500, detail="ImageKit upload failed")

        post = Post(
            user_id=user.id,
            caption=caption,
            url=response.url,
            file_type="video" if file.content_type.startswith("video/") else "image",
            file_name=response.name,
        )

        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()

@app.get("/feed")
async def  get_feed(
        session:AsyncSession=Depends(get_async_session),
        user:User=Depends(current_active_user)
):
    result=await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts=[row[0] for row in result.all()]

    result=await session.execute(select(User))
    users=[row[0] for row in result.all()]
    user_dict={u.id : u.email for u in users}


    posts_data=[]
    for post in posts:
        posts_data.append(
            {
                "id":str(post.id),
                "user_id":str(post.user_id),
                "caption":post.caption,
                "url":post.url,
                "file_type":post.file_type,
                "file_name":post.file_name,
                "created_at":post.created_at.isoformat(),
                "is_owner": post.user_id == user.id,
                "email": user_dict.get(post.user_id, "unknown"),
            }
        )
    return {"posts":posts_data}

@app.delete("/delete/{post_id}")
async def delete_post(post_id:str,session:AsyncSession=Depends(get_async_session),user:User=Depends(current_active_user)):
    try:
        post_uuid=uuid.UUID(post_id)
        result=await session.execute(select(Post).where(Post.id==post_uuid))
        post=result.scalars().first()

        if not post:
            raise HTTPException(status_code=404,detail="Post not found")

        if post.user_id != user.id:
            raise HTTPException(status_code=403,detail="Not authorized to delete this post")
        await session.delete(post)
        await session.commit()

        return {"success":True,"message":"Post  deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))








#
# text_posts = {
#     1: {
#         "title": "Messi Leads Inter Miami to Dramatic Win",
#         "content": "Lionel Messi scored a late free-kick as Inter Miami secured a dramatic victory, continuing their unbeaten run in the league."
#     },
#     2: {
#         "title": "Manchester City Extend Premier League Dominance",
#         "content": "Manchester City showcased their depth and control as they comfortably won their latest Premier League fixture."
#     },
#     3: {
#         "title": "Real Madrid Secure Last-Minute Champions League Qualification",
#         "content": "A stoppage-time goal helped Real Madrid clinch qualification, once again proving their reputation in European competitions."
#     },
#     4: {
#         "title": "Arsenal’s Young Squad Impresses Fans",
#         "content": "Arsenal’s young players delivered a confident performance, highlighting the club’s long-term rebuilding strategy."
#     },
#     5: {
#         "title": "Bayern Munich Continue Bundesliga Goal Spree",
#         "content": "Bayern Munich scored multiple goals once again, maintaining their position at the top of the Bundesliga table."
#     },
#     6: {
#         "title": "Cristiano Ronaldo Reaches New Career Milestone",
#         "content": "Cristiano Ronaldo added another milestone to his legendary career with a decisive goal in the latest match."
#     },
#     7: {
#         "title": "Barcelona Focus on Youth Development",
#         "content": "Barcelona relied heavily on academy graduates in their recent match, signaling a shift toward long-term sustainability."
#     },
#     8: {
#         "title": "Liverpool Secure Crucial Away Victory",
#         "content": "Liverpool earned a crucial away win, keeping their title hopes alive with a disciplined defensive display."
#     },
#     9: {
#         "title": "PSG Dominate Ligue 1 Fixture",
#         "content": "Paris Saint-Germain controlled possession and tempo throughout the match, securing an easy win at home."
#     },
#     10: {
#         "title": "Underdogs Shock Fans with Cup Upset",
#         "content": "A lower-division team stunned supporters by knocking out a top club in a surprising cup competition result."
#     }
# }
#
#
# @app.get("/health")
# def health():
#     return {"message": "i am alive"}
#
# @app.get("/posts")
# def get_all_posts(limit:int=None):
#     if limit:
#         return list(text_posts.values())[:limit]
#     return text_posts
#
# @app.get("/posts/{id}")
# def get_post(id:int)->PostResponse:
#     if id not in text_posts:
#         raise HTTPException(status_code=404,detail="post not found")
#     return text_posts.get(id)
#
# @app.post("/posts")
# def create_post(post: PostCreate)->PostResponse:
#     new_post={"title":post.title,"content":post.content}
#     text_posts[max(text_posts.keys()) + 1]=new_post
#     return new_post
