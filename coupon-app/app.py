import os
import uuid
import qrcode
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

# Use your Vercel deployment base URL here
BASE_URL = "https://coupon-app-lhbd.vercel.app"

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key'  # Replace with a secure value
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coupons.db'
app.config['UPLOAD_FOLDER'] = 'static/qr_codes'

# Email configuration (use app password for Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sonucocbodat@gmail.com'
app.config['MAIL_PASSWORD'] = 'lohr pkrm bhur gpjd'
app.config['MAIL_DEFAULT_SENDER'] = 'sonucocbodat@gmail.com'

mail = Mail(app)
db = SQLAlchemy(app)

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    redeemed = db.Column(db.Boolean, default=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        emails = request.form['emails'].split(',')
        for email in emails:
            email = email.strip()
            code = str(uuid.uuid4())
            qr_url = f"{BASE_URL}/redeem/{code}"
            qr_img = qrcode.make(qr_url)
            qr_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{code}.png")
            qr_img.save(qr_path)

            coupon = Coupon(email=email, code=code)
            db.session.add(coupon)
            db.session.commit()

            msg = Message('Your QR Coupon', recipients=[email])
            msg.body = f"Scan the attached QR to redeem your coupon or visit: {qr_url}"
            with open(qr_path, 'rb') as f:
                msg.attach(f"{code}.png", 'image/png', f.read())
            mail.send(msg)

        flash("Coupons sent successfully!", "success")
        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/redeem/<code>', methods=['GET', 'POST'])
def redeem(code):
    coupon = Coupon.query.filter_by(code=code).first()

    if not coupon:
        return "Invalid or expired coupon."

    if request.method == 'POST' and not coupon.redeemed:
        coupon.redeemed = True
        db.session.commit()

    return render_template('redeem.html', coupon=coupon)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)