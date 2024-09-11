from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from email.message import EmailMessage
import smtplib
import os
import sqlite3
import logging
import sys

app = Flask(__name__)
CORS(app)  # Configura o CORS

availability = {}

app.config["MAIL_SERVER"] = "smtp.office365.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "kingbarbeariaapp@outlook.com"
app.config["MAIL_PASSWORD"] = "cpf25910638"
app.config["MAIL_DEFAULT_SENDER"] = "kingbarbeariaapp@outlook.com"


mail = Mail(app)


# Caminho do banco de dados SQLite
DATABASE = os.environ.get(
    "/home/KinkBarbearia/mysite/",
    os.path.join(os.path.dirname(__file__), "kingbarbearia.db"),
)

# Configuração de logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Criar tabelas no banco de dados
def create_tables():
    conn = get_db_connection()

    # Tabela de Usuários
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE,
            photo BLOB,
            default_photo_url TEXT
        )
    """
    )

    # Tabela de Barbeiros
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS barbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """
    )

    # Tabela de Agendamentos
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barber_id INTEGER NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER NOT NULL,
            service TEXT,
            value REAL,
            client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            FOREIGN KEY (barber_id) REFERENCES barbers(id)
        )
    """
    )
    # Tabela de Transações
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barber_name TEXT NOT NULL,
            service TEXT NOT NULL,
            value REAL NOT NULL,
            date TEXT NOT NULL
        )
    """
    )

    conn.commit()
    conn.close()


# Inicializar o banco de dados
create_tables()


def send_email_notification(booking):
    msg = EmailMessage()
    msg.set_content(
        f"""
        Novo agendamento:
        Barbeiro: {booking['barber']}
        Data: {booking['date']}
        Hora: {booking['time']}
        Duração: {booking['duration']} minutos
        Serviço: {booking['service']}
        Valor: {booking['value']}
        Nome do cliente: {booking['client_name']}
        Telefone do cliente: {booking['client_phone']}
    """
    )
    msg["Subject"] = "Novo Agendamento"
    msg["From"] = "kingbarbeariaapp@outlook.com"
    msg["To"] = "kingbarbeariaapp@outlook.com"

    with smtplib.SMTP("smtp.outlook.com", 587) as server:
        server.starttls()
        server.login("kingbarbeariaapp@outlook.com", "cpf25910638")
        server.send_message(msg)


# Inserir barbeiros iniciais
def insert_initial_barbers():
    conn = get_db_connection()
    conn.execute("INSERT INTO barbers (name) VALUES ('Wallace')")
    conn.execute("INSERT INTO barbers (name) VALUES ('Mateus')")
    conn.commit()
    conn.close()


insert_initial_barbers()


@app.route("/register", methods=["POST"])
def register_user():
    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email", "")  # Email é opcional

    logging.debug(f"Recebido: name={name}, phone={phone}, email={email}")

    if not name or not phone:
        logging.warning("Nome e telefone são obrigatórios.")
        return jsonify({"message": "Nome e telefone são obrigatórios."}), 400

    conn = None
    try:
        conn = get_db_connection()
        user_exists = conn.execute(
            "SELECT * FROM users WHERE name = ? AND phone = ?", (name, phone)
        ).fetchone()

        if user_exists:
            return jsonify({"message": "Usuário já cadastrado"}), 400

        conn.execute(
            "INSERT INTO users (name, phone, email) VALUES (?, ?, ?)",
            (name, phone, email),
        )
        conn.commit()
        logging.info(f"Usuário cadastrado com sucesso: {name}")
        return jsonify({"message": "Usuário cadastrado com sucesso!"})

    except Exception as e:
        logging.error(f"Erro ao cadastrar usuário: {e}")
        return jsonify({"message": "Erro ao cadastrar usuário"}), 500

    finally:
        if conn:
            conn.close()


@app.route("/users", methods=["GET"])
def get_all_users():
    try:
        conn = get_db_connection()
        users = conn.execute("SELECT * FROM users").fetchall()
        conn.close()
        users_list = [dict(user) for user in users]
        return jsonify(users_list), 200
    except Exception as e:
        logging.error(f"Erro ao recuperar usuários: {e}")
        return jsonify({"message": "Erro ao recuperar usuários"}), 500


@app.route("/get_user", methods=["GET"])
def get_user():
    name = request.args.get("name")
    phone = request.args.get("phone")

    if not name or not phone:
        logging.warning("Nome ou telefone não fornecidos na requisição GET /get_user")
        return jsonify({"message": "Nome e telefone devem ser fornecidos"}), 400

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE name = ? AND phone = ?", (name, phone)
    ).fetchone()
    conn.close()

    if not user:
        logging.info(f"Usuário não encontrado: nome={name}, telefone={phone}")
        return jsonify({"message": "Usuário não encontrado"}), 404

    user_data = {key: user[key] for key in user.keys()}
    logging.info(f"Usuário encontrado: {user_data}")
    return jsonify(user_data), 200


@app.route("/get_users_all", methods=["GET"])
def get_users_all():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    if not users:
        logging.info("Nenhum usuário encontrado na requisição GET /get_users_all")
        return jsonify({"message": "Nenhum usuário encontrado"}), 404

    # Converte os dados dos usuários para um formato de lista de dicionários
    users_data = [{key: user[key] for key in user.keys()} for user in users]
    logging.info(f"{len(users_data)} usuários encontrados")
    return jsonify(users_data), 200


@app.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    name = data.get("name")
    phone = data.get("phone")

    if not name or not phone:
        logging.warning("Nome ou telefone não fornecidos na requisição POST /login")
        return jsonify({"message": "Nome e telefone devem ser fornecidos"}), 400

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE name = ? AND phone = ?", (name, phone)
    ).fetchone()
    conn.close()

    if not user:
        logging.info(f"Falha no login: nome={name}, telefone={phone}")
        return jsonify({"message": "Usuário ou senha inválidos"}), 401

    logging.info(f"Login bem-sucedido: nome={name}, telefone={phone}")
    return jsonify({"message": "Login successful!"}), 200


availability = {"Wallace": [], "Mateus": []}


def is_time_slot_available(barber, date, time, duration):
    booking_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    booking_end = booking_start + timedelta(minutes=duration)

    for booking in availability.get(barber, []):
        existing_start = datetime.strptime(
            f"{booking['date']} {booking['time']}", "%Y-%m-%d %H:%M"
        )
        existing_end = existing_start + timedelta(minutes=booking["duration"])

        if not (booking_end <= existing_start or booking_start >= existing_end):
            return False

        if not is_time_slot_available(barber, date, time, duration):
            return jsonify({"error": "Time slot is not available"}), 400

    return True


@app.route("/schedule", methods=["POST"])
def schedule_appointment():
    data = request.get_json()
    barber = data.get("barber")
    date = data.get("date")
    time = data.get("time")
    duration = int(data.get("duration", 40))

    if not barber or not time or not date:
        return jsonify({"error": "Barber, date, and time are required"}), 400

    try:
        booking_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Invalid date or time format"}), 400

    booking_end = booking_start + timedelta(minutes=duration)

    for booking in availability.get(barber, []):
        existing_start = datetime.strptime(
            f"{booking['date']} {booking['time']}", "%Y-%m-%d %H:%M"
        )
        existing_end = existing_start + timedelta(minutes=booking["duration"])

        if booking_start < existing_end and booking_end > existing_start:
            return (
                jsonify({"error": "Barber is not available at the selected time"}),
                409,
            )

    new_id = (
        max([booking["id"] for booking in availability.get(barber, [])], default=0) + 1
    )

    new_booking = {
        "id": new_id,
        "date": date,
        "time": time,
        "duration": duration,
        "service": data.get("service", "Undefined service"),
        "value": data.get("value", 0),
        "client_name": data.get("name", "Unknown client"),
        "client_phone": data.get("phone", "No phone number"),
        "client_email": data.get("email"),
        "barber": barber,
    }

    availability.setdefault(barber, []).append(new_booking)

    print(f"Agendamento adicionado para o barbeiro {barber}: {new_booking}")

    # Enviar email de notificação
    send_email_notification(new_booking)

    return jsonify(new_booking), 201


@app.route("/availability", methods=["GET"])
def get_availability():
    barber = request.args.get("barber")
    date = request.args.get("date")

    if not barber or not date:
        return jsonify({"error": "Barber and date are required"}), 400

    if barber not in availability:
        return jsonify({"error": "Barber not found"}), 404

    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("19:00", "%H:%M")
    step = timedelta(minutes=30)

    available_times = []
    current_time = start_time
    while current_time < end_time:
        is_available = True
        for booking in availability[barber]:
            if booking["date"] == date:
                booking_start = datetime.strptime(booking["time"], "%H:%M")
                booking_end = booking_start + timedelta(minutes=booking["duration"])

                if (
                    booking_start <= current_time < booking_end
                    or booking_start < current_time + step <= booking_end
                ):
                    is_available = False
                    break

        if is_available:
            available_times.append(current_time.strftime("%H:%M"))

        current_time += step

    return jsonify({"available_times": available_times})


@app.route("/customer_bookings", methods=["GET"])
def get_customer_bookings():
    name = request.args.get("name")
    phone = request.args.get("phone")

    if not name or not phone:
        return jsonify({"error": "Name and phone are required"}), 400

    # Verifica se o cliente está no banco de dados
    customer_bookings = []
    for barber, bookings in availability.items():
        for booking in bookings:
            if booking["client_name"] == name and booking["client_phone"] == phone:
                customer_bookings.append(
                    {
                        "id": booking["id"],  # Inclui o ID do agendamento
                        "service": booking["service"],
                        "barber": barber,
                        "date": booking["date"],
                        "time": booking["time"],
                        "duration": booking["duration"],
                        "valueservice": booking["value"],
                    }
                )

    if not customer_bookings:
        return jsonify([]), 200  # Retorna lista vazia se não houver agendamentos

    return jsonify(customer_bookings), 200


@app.route("/customer_bookings/<int:booking_id>", methods=["DELETE"])
def delete_customer_booking(booking_id):
    booking_found = False

    for barber, bookings in availability.items():
        for booking in bookings:
            if booking["id"] == booking_id:
                bookings.remove(booking)
                booking_found = True
                break

        if booking_found:
            break

    if not booking_found:
        return jsonify({"error": "Booking not found"}), 404

    return jsonify({"message": "Booking deleted successfully"}), 200


@app.route("/appointments", methods=["GET"])
def get_appointments():
    barber = request.args.get("barber")
    date = request.args.get("date")

    if not barber:
        return jsonify({"error": "Barber is required"}), 400

    if barber not in availability:
        return jsonify({"error": "Barber not found"}), 404

    filtered_appointments = [
        appointment
        for appointment in availability[barber]
        if not date or appointment["date"] == date
    ]

    if not filtered_appointments:
        return jsonify({"message": "No appointments found"}), 404

    return jsonify({"appointments": filtered_appointments}), 200


@app.route("/appointments/<int:appointment_id>", methods=["DELETE"])
def delete_appointment(appointment_id):
    barber = request.args.get("barber")

    if not barber:
        return jsonify({"error": "Barber is required"}), 400

    if barber not in availability:
        return jsonify({"error": "Barber not found"}), 404

    appointment_to_delete = None
    for appointment in availability[barber]:
        if appointment["id"] == appointment_id:
            appointment_to_delete = appointment
            break

    if appointment_to_delete:
        availability[barber].remove(appointment_to_delete)
        return jsonify({"message": "Appointment deleted successfully"}), 200
    else:
        return jsonify({"error": "Appointment not found"}), 404


@app.route("/caixa", methods=["POST"])
def add_transaction():
    data = request.get_json()
    barber_name = data.get("barber_name")
    service = data.get("service")
    value = float(data.get("value").replace("R$", "").replace(",", ".").strip())
    date = data.get("date")

    if not barber_name or not service or not value or not date:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO transactions (barber_name, service, value, date)
        VALUES (?, ?, ?, ?)
    """,
        (barber_name, service, value, date),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction added successfully"}), 201


@app.route("/caixa", methods=["GET"])
def get_daily_cash():
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "Date is required"}), 400

    conn = get_db_connection()
    transactions = conn.execute(
        """
        SELECT barber_name, SUM(value) as total
        FROM transactions
        WHERE date = ?
        GROUP BY barber_name
    """,
        (date,),
    ).fetchall()
    conn.close()

    if not transactions:
        return jsonify({"message": "No transactions found for this date"}), 404

    result = []
    for transaction in transactions:
        result.append(
            {
                "barber_name": transaction["barber_name"],
                "total_cash": f"R$ {transaction['total']:.2f}",
            }
        )


@app.route("/test-email", methods=["GET"])
def test_email():
    try:
        msg = Message(
            subject="Teste de E-mail",
            recipients=["kingbarbeariaapp@outlook.com"],  # Substitua pelo seu e-mail
            body="Este é um e-mail de teste.",
        )
        mail.send(msg)
        return jsonify({"message": "E-mail de teste enviado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result), 200


if __name__ == "__main__":
    # Remova o modo de depuração e ajuste a porta conforme necessário
    app.run(host="192.168.15.5", port=5090, debug=False)
