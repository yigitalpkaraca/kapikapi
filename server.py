from flask import Flask,redirect,url_for,render_template,request,session
from flask_sqlalchemy import SQLAlchemy








app = Flask(__name__)
# --------------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///veritabani.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key='kapikapi123'
db = SQLAlchemy(app)
# --------------------------------------------------------------------

# -----------------------DATABASE DENEME------------------------

class User(db.Model):
    
    __tablename__ = 'user' 
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)















# Ana Sayfa (index.html)
@app.route("/")
def home():
    return render_template('index.html')

# Gönderi Oluştur (send.html)
@app.route("/gonder")
def send():
    return render_template('send.html')

# Gönderi Takip (track.html)
@app.route("/takip")
def track():
    return render_template('track.html')

# Kurye Ol (courier.html)
@app.route("/kurye-ol")
def courier():
    return render_template('courier.html')

# Giriş Yap (login.html)
@app.route("/giris",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        girilen_email = request.form.get('email')
        girilen_sifre = request.form.get('password')

        # Veritabanında bu e-posta ile kayıtlı kullanıcıyı bul 
        user = User.query.filter_by(email=girilen_email).first()

        if user and user.password == girilen_sifre:
            # Giriş başarılı! Kullanıcıyı oturuma kaydet
            session['user_id'] = user.id
            session['user_name'] = user.fullname
            return redirect(url_for('home'))
        else:
            # Hatalı giriş durumu
            return "E-posta veya şifre hatalı! Lütfen tekrar dene." 
    
    
    
    return render_template('login.html')

# Kayıt Ol (register.html)
@app.route("/kayit",methods=['GET','POST'])
def register():
    if request.method =='POST':
        ad = request.form.get('fullname')
        email = request.form.get('email')
        sifre = request.form.get('password')
        # sifre = request.form.get('password')
        tel = request.form.get('phone')

        yeni_uye = User(fullname=ad,email = email,password=sifre,phone = tel)
        db.session.add(yeni_uye)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/cikis")
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ =="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)




