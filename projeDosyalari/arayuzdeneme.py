from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import psycopg2
import json
from datetime import date

app = Flask(__name__)
app.secret_key = "supersecretkey"

def connect_to_db():
    return psycopg2.connect(
        host="localhost",
        database="eNabiz2",
        user="postgres",
        password="admin"
    )

def ekle_hastalar(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        hastalar_listesi = json.load(file)

    conn = connect_to_db()
    cur = conn.cursor()

    for hasta in hastalar_listesi:
        ad = hasta['Ad']
        soyad = hasta['Soyad']
        dogum_tarihi = hasta['DogumTarihi']
        cinsiyet = hasta['Cinsiyet']
        telefon_numarasi = hasta['TelefonNumarasi']
        adres = hasta['Adres']

        cur.execute(
            """
            INSERT INTO Hastalar (Ad, Soyad, DogumTarihi, Cinsiyet, TelefonNumarasi, Adres)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (TelefonNumarasi)
            DO UPDATE SET
                Ad = EXCLUDED.Ad,
                Soyad = EXCLUDED.Soyad,
                DogumTarihi = EXCLUDED.DogumTarihi,
                Cinsiyet = EXCLUDED.Cinsiyet,
                Adres = EXCLUDED.Adres
            """,
            (ad, soyad, dogum_tarihi, cinsiyet, telefon_numarasi, adres)
        )

    conn.commit()
    cur.close()
    conn.close()
    print("Hastalar eklendi veya güncellendi!")

def ekle_doktorlar(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        doktorlar_listesi = json.load(file)

    conn = connect_to_db()
    cur = conn.cursor()

    for doktor in doktorlar_listesi:
        ad = doktor['Ad']
        soyad = doktor['Soyad']
        uzmanlik_alani = doktor['UzmanlikAlani']
        calistigi_hastane = doktor['CalistigiHastane']

        cur.execute(
            """
            INSERT INTO Doktorlar (Ad, Soyad, UzmanlikAlani, CalistigiHastane)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (Ad, Soyad, UzmanlikAlani, CalistigiHastane)
            DO UPDATE SET
                UzmanlikAlani = EXCLUDED.UzmanlikAlani,
                CalistigiHastane = EXCLUDED.CalistigiHastane
            """,
            (ad, soyad, uzmanlik_alani, calistigi_hastane)
        )

    conn.commit()
    cur.close()
    conn.close()
    print("Doktorlar eklendi veya güncellendi!")

def ekle_randevular(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        randevular_listesi = json.load(file)

    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("SELECT HastaID FROM Hastalar")
    mevcut_hasta_idler = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DoktorID FROM Doktorlar")
    mevcut_doktor_idler = [row[0] for row in cur.fetchall()]

    for randevu in randevular_listesi:
        randevu_tarihi = randevu['RandevuTarihi']
        randevu_saati = randevu['RandevuSaati']
        hasta_id = randevu['HastaID']
        doktor_id = randevu['DoktorID']

        if hasta_id in mevcut_hasta_idler and doktor_id in mevcut_doktor_idler:
            cur.execute(
                """
                INSERT INTO Randevular (RandevuTarihi, RandevuSaati, HastaID, DoktorID)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (RandevuTarihi, RandevuSaati, HastaID, DoktorID)
                DO NOTHING
                """,
                (randevu_tarihi, randevu_saati, hasta_id, doktor_id)
            )

    conn.commit()
    cur.close()
    conn.close()
    print("Randevular eklendi!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hastalar')
def hastalar():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Hastalar")
    total_patients = cur.fetchone()[0]

    cur.execute("SELECT * FROM Hastalar ORDER BY HastaID LIMIT %s OFFSET %s", (per_page, offset))
    hastalar = cur.fetchall()

    cur.close()
    conn.close()

    next_url = url_for('hastalar', page=page + 1) if offset + per_page < total_patients else None
    prev_url = url_for('hastalar', page=page - 1) if page > 1 else None

    return render_template('hastalar.html', hastalar=hastalar, next_url=next_url, prev_url=prev_url)

@app.route('/doktorlar')
def doktorlar():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Doktorlar")
    total_doctors = cur.fetchone()[0]

    cur.execute("SELECT * FROM Doktorlar ORDER BY DoktorID LIMIT %s OFFSET %s", (per_page, offset))
    doktorlar = cur.fetchall()

    cur.close()
    conn.close()

    next_url = url_for('doktorlar', page=page + 1) if offset + per_page < total_doctors else None
    prev_url = url_for('doktorlar', page=page - 1) if page > 1 else None

    return render_template('doktorlar.html', doktorlar=doktorlar, next_url=next_url, prev_url=prev_url)

@app.route('/randevular')
def randevular():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Randevular")
    total_appointments = cur.fetchone()[0]

    cur.execute("SELECT RandevuID, HastaID, DoktorID, RandevuTarihi, RandevuSaati FROM Randevular ORDER BY RandevuID LIMIT %s OFFSET %s", (per_page, offset))
    randevular = cur.fetchall()

    cur.close()
    conn.close()

    next_url = url_for('randevular', page=page + 1) if offset + per_page < total_appointments else None
    prev_url = url_for('randevular', page=page - 1) if page > 1 else None

    return render_template('randevular.html', randevular=randevular, next_url=next_url, prev_url=prev_url)

@app.route('/doktorlar_getir/<uzmanlik_alani>')
def doktorlar_getir(uzmanlik_alani):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("SELECT DoktorID, Ad, Soyad FROM Doktorlar WHERE UzmanlikAlani = %s ORDER BY Ad, Soyad", (uzmanlik_alani,))
    doktorlar = cur.fetchall()
    cur.close()
    conn.close()
    doktorlar_json = [{"doktor_id": doktor[0], "ad": doktor[1], "soyad": doktor[2]} for doktor in doktorlar]
    return jsonify({"doktorlar": doktorlar_json})


@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT UzmanlikAlani FROM Doktorlar ORDER BY UzmanlikAlani")
    uzmanlik_alanlari = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT CalistigiHastane FROM Doktorlar ORDER BY CalistigiHastane")
    hastaneler = [row[0] for row in cur.fetchall()]

    if request.method == 'POST':
        kullanici_turu = request.form['kullanici_turu']
        ad = request.form['ad']
        soyad = request.form['soyad']


        if kullanici_turu == 'Hasta':
            dogum_tarihi = request.form['dogum_tarihi']
            cinsiyet = request.form['cinsiyet']
            telefon_numarasi = request.form['telefon_numarasi']
            adres = request.form['adres']

            cur.execute(
                """
                INSERT INTO Hastalar (Ad, Soyad, DogumTarihi, Cinsiyet, TelefonNumarasi, Adres)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (ad, soyad, dogum_tarihi, cinsiyet, telefon_numarasi, adres)
            )
            conn.commit()
            flash("Hasta kaydı başarılı!", "success")

        elif kullanici_turu == 'Doktor':
            uzmanlik_alani = request.form['uzmanlik_alani']
            calistigi_hastane = request.form['calistigi_hastane']

            cur.execute(
                """
                INSERT INTO Doktorlar (Ad, Soyad, UzmanlikAlani, CalistigiHastane)
                VALUES (%s, %s, %s, %s)
                """,
                (ad, soyad, uzmanlik_alani, calistigi_hastane)
            )
            conn.commit()
            flash("Doktor kaydı başarılı!", "success")

        return redirect(url_for('login'))

    cur.close()
    conn.close()

    return render_template('register.html', uzmanlik_alanlari=uzmanlik_alanlari, hastaneler=hastaneler)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        kullanici_turu = request.form['kullanici_turu']

        conn = connect_to_db()
        cur = conn.cursor()

        if kullanici_turu == 'Hasta':
            cur.execute("SELECT * FROM Hastalar WHERE Ad = %s AND Soyad = %s", (ad, soyad))
            user = cur.fetchone()
        elif kullanici_turu == 'Doktor':
            cur.execute("SELECT * FROM Doktorlar WHERE Ad = %s AND Soyad = %s", (ad, soyad))
            user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session['loggedin'] = True
            session['user_id'] = user[0]
            session['user_type'] = kullanici_turu
            flash("Giriş başarılı!")
            return redirect(url_for('index'))
        else:
            flash("Geçersiz kullanıcı adı veya soyadı!")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('user_type', None)
    flash("Başarıyla çıkış yaptınız!")
    return redirect(url_for('index'))

@app.route('/hasta_randevularim')
def hasta_randevularim():
    if 'ad' in session and session['kullanici_turu'] == 'Hasta':
        ad = session['ad']
        soyad = session['soyad']

        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.RandevuTarihi, r.RandevuSaati, d.Ad, d.Soyad
            FROM Randevular r
            JOIN Doktorlar d ON r.DoktorID = d.DoktorID
            JOIN Hastalar h ON r.HastaID = h.HastaID
            WHERE h.Ad = %s AND h.Soyad = %s
            ORDER BY r.RandevuTarihi, r.RandevuSaati
        """, (ad, soyad))
        randevular = cur.fetchall()
        cur.close()
        conn.close()

        return render_template('hasta_randevularim.html', randevular=randevular)
    else:
        flash("Bu sayfaya erişim izniniz yok!")
        return redirect(url_for('index'))


@app.route('/doktor_hasta_randevulari')
def doktor_hasta_randevulari():
    if 'loggedin' in session and session['user_type'] == 'Doktor':
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("SELECT h.Ad, h.Soyad, r.RandevuTarihi, r.RandevuSaati FROM Randevular r JOIN Hastalar h ON r.HastaID = h.HastaID WHERE r.DoktorID = %s", (session['user_id'],))
        randevular = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('doktor_hasta_randevulari.html', randevular=randevular)
    else:
        flash("Bu sayfaya erişim yetkiniz yok!")
        return redirect(url_for('index'))

@app.route('/hasta_ekle', methods=['GET', 'POST'])
def hasta_ekle():
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        dogum_tarihi = request.form['dogum_tarihi']
        cinsiyet = request.form['cinsiyet']
        telefon_numarasi = request.form['telefon_numarasi']
        adres = request.form['adres']

        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Hastalar (Ad, Soyad, DogumTarihi, Cinsiyet, TelefonNumarasi, Adres)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (ad, soyad, dogum_tarihi, cinsiyet, telefon_numarasi, adres)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Hasta başarıyla eklendi!")
        return redirect(url_for('hastalar'))

    return render_template('hasta_ekle.html')

@app.route('/doktor_ekle', methods=['GET', 'POST'])
def doktor_ekle():
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        uzmanlik_alani = request.form['uzmanlik_alani']
        calistigi_hastane = request.form['calistigi_hastane']

        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Doktorlar (Ad, Soyad, UzmanlikAlani, CalistigiHastane)
            VALUES (%s, %s, %s, %s)
            """,
            (ad, soyad, uzmanlik_alani, calistigi_hastane)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Doktor başarıyla eklendi!")
        return redirect(url_for('doktorlar'))

    return render_template('doktor_ekle.html')

@app.route('/randevu_ekle', methods=['GET', 'POST'])
def randevu_ekle():
    conn = connect_to_db()
    cur = conn.cursor()

    if request.method == 'POST':
        hasta_id = request.form['hasta_id']
        doktor_id = request.form['doktor_id']
        randevu_tarihi = request.form['randevu_tarihi']
        randevu_saati = request.form['randevu_saati']

        if randevu_tarihi < date.today().strftime('%Y-%m-%d'):
            flash("Randevu tarihi geçmiş olamaz!", "danger")
            return redirect(url_for('randevu_ekle'))

        cur.execute(
            """
            INSERT INTO Randevular (HastaID, DoktorID, RandevuTarihi, RandevuSaati)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (RandevuID) DO NOTHING
            """,
            (hasta_id, doktor_id, randevu_tarihi, randevu_saati)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Randevu başarıyla eklendi!")
        return redirect(url_for('randevular'))

    cur.execute("SELECT HastaID, Ad, Soyad FROM Hastalar ORDER BY Ad, Soyad")
    hastalar = cur.fetchall()

    cur.execute("SELECT DISTINCT UzmanlikAlani FROM Doktorlar ORDER BY UzmanlikAlani")
    uzmanlik_alanlari = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('randevu_ekle.html', hastalar=hastalar, uzmanlik_alanlari=[uzmanlik[0] for uzmanlik in uzmanlik_alanlari])

@app.route('/hasta_guncelle/<int:hasta_id>', methods=['GET', 'POST'])
def hasta_guncelle(hasta_id):
    conn = connect_to_db()
    cur = conn.cursor()

    if request.method == 'POST':
        telefon_numarasi = request.form['telefon_numarasi']
        adres = request.form['adres']

        cur.execute(
            """
            UPDATE Hastalar
            SET TelefonNumarasi = %s, Adres = %s
            WHERE HastaID = %s
            """,
            (telefon_numarasi, adres, hasta_id)
        )
        conn.commit()

        flash("Hasta başarıyla güncellendi!")
        return redirect(url_for('hastalar'))

    cur.execute("SELECT * FROM Hastalar WHERE HastaID = %s", (hasta_id,))
    hasta = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('hasta_guncelle.html', hasta=hasta)


@app.route('/doktor_guncelle/<int:doktor_id>', methods=['GET', 'POST'])
def doktor_guncelle(doktor_id):
    conn = connect_to_db()
    cur = conn.cursor()

    if request.method == 'POST':
        calistigi_hastane = request.form['calistigi_hastane']

        cur.execute(
            """
            UPDATE Doktorlar
            SET CalistigiHastane = %s
            WHERE DoktorID = %s
            """,
            (calistigi_hastane, doktor_id)
        )
        conn.commit()

        flash("Doktor başarıyla güncellendi!")
        return redirect(url_for('doktorlar'))

    cur.execute("SELECT * FROM Doktorlar WHERE DoktorID = %s", (doktor_id,))
    doktor = cur.fetchone()

    cur.execute("SELECT DISTINCT CalistigiHastane FROM Doktorlar")
    hastaneler = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('doktor_guncelle.html', doktor=doktor, hastaneler=hastaneler)


@app.route('/randevu_guncelle/<int:randevu_id>', methods=['GET', 'POST'])
def randevu_guncelle(randevu_id):
    conn = connect_to_db()
    cur = conn.cursor()

    if request.method == 'POST':
        doktor_id = request.form['doktor_id']
        randevu_tarihi = request.form['randevu_tarihi']
        randevu_saati = request.form['randevu_saati']

        cur.execute(
            """
            UPDATE Randevular
            SET DoktorID = %s, RandevuTarihi = %s, RandevuSaati = %s
            WHERE RandevuID = %s
            """,
            (doktor_id, randevu_tarihi, randevu_saati, randevu_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Randevu başarıyla güncellendi!")
        return redirect(url_for('randevular'))

    cur.execute(
        """
        SELECT r.RandevuID, r.HastaID, r.DoktorID, r.RandevuTarihi, r.RandevuSaati, h.Ad, h.Soyad, d.UzmanlikAlani, d.Ad, d.Soyad
        FROM Randevular r
        JOIN Hastalar h ON r.HastaID = h.HastaID
        JOIN Doktorlar d ON r.DoktorID = d.DoktorID
        WHERE r.RandevuID = %s
        """,
        (randevu_id,)
    )
    randevu = cur.fetchone()

    cur.execute("SELECT DISTINCT UzmanlikAlani FROM Doktorlar ORDER BY UzmanlikAlani")
    uzmanlik_alanlari = cur.fetchall()

    cur.close()
    conn.close()

    current_date = date.today().strftime('%Y-%m-%d')
    return render_template('randevu_guncelle.html', randevu=randevu, uzmanlik_alanlari=[uzmanlik[0] for uzmanlik in uzmanlik_alanlari], current_date=current_date)


@app.route('/hasta_sil/<int:hasta_id>', methods=['POST'])
def hasta_sil(hasta_id):
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM Hastalar WHERE HastaID = %s", (hasta_id,))
    conn.commit()

    flash("Hasta ve ilgili tüm randevuları başarıyla silindi!")

    cur.close()
    conn.close()

    return redirect(url_for('hastalar'))


@app.route('/doktor_sil/<int:doktor_id>', methods=['POST'])
def doktor_sil(doktor_id):
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM Doktorlar WHERE DoktorID = %s", (doktor_id,))
    conn.commit()

    flash("Doktor ve ilgili tüm randevuları başarıyla silindi!")

    cur.close()
    conn.close()

    return redirect(url_for('doktorlar'))


@app.route('/randevu_sil/<int:randevu_id>', methods=['POST'])
def randevu_sil(randevu_id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM Randevular WHERE RandevuID = %s", (randevu_id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Randevu başarıyla silindi!")
    return redirect(url_for('randevular'))


@app.route('/doktor_hastagor/<int:doktor_id>')
def doktor_hastagor(doktor_id):
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT h.HastaID, h.Ad, h.Soyad, h.DogumTarihi, h.Cinsiyet, h.TelefonNumarasi, h.Adres
        FROM Hastalar h
        JOIN Randevular r ON h.HastaID = r.HastaID
        WHERE r.DoktorID = %s
        ORDER BY h.Ad, h.Soyad
    """, (doktor_id,))

    hastalar = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('doktor_hastagor.html', hastalar=hastalar)



if __name__ == '__main__':
    app.run(debug=True)
