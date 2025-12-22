from flask import Flask, request, abort, render_template, send_file, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from math import ceil
from utils.models import Photo, Base
import os, datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # ./images 디렉토리 없으면 생성

engine = create_engine('sqlite:///db.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()

@app.route("/", methods=["GET"])
def main():
    page = request.args.get("page", 1, type=int)

    per_page = 12  # 한 페이지당 사진 수

    total = db_session.query(Photo).filter(Photo.upload ==True).count()
    total_pages = ceil(total / per_page)

    photos = (
        db_session.query(Photo)
        .filter(Photo.upload == True)
        .order_by(desc(Photo.createdAt))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return render_template(
        "index.html",
        photos=photos,
        page=page,
        total_pages=total_pages
    )

@app.route("/photo", methods=["GET"])
def photo():
    session = request.args.get("session")

    if not session:
        return render_template('forbidden.html')
    
    if os.path.exists(f"./images/{session}.png"):
        photo = db_session.query(Photo).filter_by(id=session).first()
        return render_template('photo.html', session=session, image_path=f'./download_image?session={session}', photo=photo)

    return jsonify({
        "message": "다음 이미지가 없어요."
    }), 404

@app.route("/upload", methods=["POST"])
def upload():
    password = request.args.get("password")

    if not password or password != "8krybwTfjJEIFq8J50CfEJlyFMlxYNl04pZDcgXKPz8pY3E362":  # 비밀번호 확인 (예: 1234)
        abort(403)

    print(request.files)

    if 'file' not in request.files:
        return {'result': False, 'message': 'file 파라미터가 없습니다.'}, 400

    file = request.files['file']

    if file.filename == '':
        return {'result': False, 'message': '파일명이 없습니다.'}, 400
    
    upload = request.form.get("upload") == "true"

    if not upload:
        upload = False

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    session_id = file.filename.split(".")[0]

    photo = Photo(
        id=session_id,
        photoUrl=f"http://localhost:8000/get_image?session={session_id}",
        createdAt=datetime.datetime.utcnow(),
        like=0,
        upload=upload
    )

    db_session.add(photo)
    db_session.commit()

    return {'result': True, 'message': f'{file.filename} 저장 완료'}, 200

@app.route("/likes", methods=["GET"])
def likes():
    page = request.args.get("page", 1, type=int)
    per_page = 12

    photos = (
        db_session.query(Photo)
        .filter(Photo.upload == True)
        .order_by(Photo.like.desc(), Photo.createdAt.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total = db_session.query(Photo).filter(Photo.upload == True).count()
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "likes.html",
        photos=photos,
        page=page,
        total_pages=total_pages
    )

@app.route("/api/like", methods=["POST"])
def like_photo():
    data = request.get_json()
    session = data.get("session")

    if not session:
        return jsonify({"result": False, "message": "session 누락"}), 400

    photo = db_session.query(Photo).filter(Photo.id == session).first()

    if not photo:
        return jsonify({"result": False, "message": "사진 없음"}), 404

    photo.like += 1
    db_session.commit()

    return jsonify({
        "result": True,
        "like": photo.like
    })

@app.route("/download", methods=["GET"])
def download():
    session = request.args.get('session') # http://#DOMAIN/download?session={uuid}
    if not session:
        return render_template('forbidden.html')
    
    if os.path.exists(f"./images/{session}.png"):
        return render_template('download.html', session=session, image_path=f'./download_image?session={session}')
    
    return jsonify({
        "message": "다음 이미지가 없어요."
    }), 404

@app.route('/download_image', methods=["GET"])
def download_image():
    session = request.args.get('session')
    if not session:
        return render_template('forbidden.html')
    
    if os.path.exists(f"./images/{session}.png"):
        return send_file(f'./images/{session}.png', as_attachment=True)

    return jsonify({
        "message": "다음 이미지가 없어요."
    }), 404

@app.route('/get_image', methods=["GET"])
def get_image():
    session = request.args.get('session')
    print(f"./images/{session}.png")
    if not session:
        return render_template('forbidden.html')
    
    if os.path.exists(f"./images/{session}.png"):
        return send_file(f'./images/{session}.png')
    
    return jsonify({
        "message": "다음 이미지가 없어요."
    }), 404

if __name__ == "__main__":
    app.run(port=8000, debug=True)
