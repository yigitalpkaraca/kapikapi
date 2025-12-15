from flask import Flask,redirect,url_for,render_template

app = Flask(__name__)





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
@app.route("/giris")
def login():
    return render_template('login.html')

# Kayıt Ol (register.html)
@app.route("/kayit")
def register():
    return render_template('register.html')

if __name__ =="__main__":
    app.run(debug=True)





