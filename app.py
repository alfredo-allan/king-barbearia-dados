from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

# from flask_mail import Mail, Message
# from email.message import EmailMessage
# import smtplib
import os
import sqlite3
import logging
import sys
import bcrypt

app = Flask(__name__)
CORS(app)  # Configura o CORS

availability = {}

# # Configurações do Flask-Mail
# app.config["MAIL_SERVER"] = "smtp.office365.com"
# app.config["MAIL_PORT"] = 587
# app.config["MAIL_USE_TLS"] = True
# app.config["MAIL_USERNAME"] = "kingbarbeariaapp@outlook.com"
# app.config["MAIL_PASSWORD"] = "cpf25910638"
# app.config["MAIL_DEFAULT_SENDER"] = "kingbarbeariaapp@outlook.com"


# mail = Mail(app)


# Caminho do banco de dados SQLite
DATABASE = os.environ.get(
    "/home/KinkBarbearia/mysite/",
    os.path.join(os.path.dirname(__file__), "kingbarbearia.db"),
)

# Configuração de logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


# def send_email_notification(booking):
#     msg = Message(
#         "Novo Agendamento",
#         recipients=["kingbarbeariaapp@outlook.com"],
#         body=f"""
#         Novo agendamento:
#         Barbeiro: {booking['barber']}
#         Data: {booking['date']}
#         Hora: {booking['time']}
#         Duração: {booking['duration']} minutos
#         Serviço: {booking['service']}
#         Valor: {booking['value']}
#         Nome do cliente: {booking['client_name']}
#         Telefone do cliente: {booking['client_phone']}
#         """,
#     )

#     try:
#         with app.app_context():
#             mail.send(msg)
#         print("E-mail enviado com sucesso!")
#     except Exception as e:
#         print(f"Erro ao enviar e-mail: {e}")


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
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


# def send_email_notification(booking):
#     msg = EmailMessage()
#     msg.set_content(
#         f"""
#         Novo agendamento:
#         Barbeiro: {booking['barber']}
#         Data: {booking['date']}
#         Hora: {booking['time']}
#         Duração: {booking['duration']} minutos
#         Serviço: {booking['service']}
#         Valor: {booking['value']}
#         Nome do cliente: {booking['client_name']}
#         Telefone do cliente: {booking['client_phone']}
#     """
#     )
#     msg["Subject"] = "Novo Agendamento"
#     msg["From"] = "kingbarbeariaapp@outlook.com"
#     msg["To"] = "kingbarbeariaapp@outlook.com"

#     with smtplib.SMTP("smtp.outlook.com", 587) as server:
#         server.starttls()
#         server.login("kingbarbeariaapp@outlook.com", "cpf25910638")
#         server.send_message(msg)


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
    """Rota para registrar um novo usuário."""
    data = request.get_json()

    # Extração dos dados enviados no corpo da requisição
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    password = data.get("password")

    # Validação para garantir que todos os campos obrigatórios foram preenchidos
    if not all([name, phone, email, password]):
        return jsonify({"message": "Todos os campos são obrigatórios"}), 400

    try:
        # Gerar o hash da senha
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        conn = get_db_connection()
        # Inserção dos dados do usuário na tabela
        conn.execute(
            """
            INSERT INTO users (name, phone, email, password)
            VALUES (?, ?, ?, ?)
            """,
            (name, phone, email, hashed_password),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Usuário registrado com sucesso"}), 201
    except sqlite3.IntegrityError:
        # Caso o email já esteja registrado
        return jsonify({"message": "Email já registrado"}), 400
    except Exception as e:
        logging.error(f"Erro ao registrar usuário: {e}")
        return jsonify({"message": "Erro ao registrar usuário"}), 500


@app.route("/users", methods=["GET"])
def get_users():
    """Rota para retornar todos os usuários."""
    try:
        conn = get_db_connection()
        users = conn.execute(
            "SELECT id, name, phone, email, password FROM users"
        ).fetchall()
        conn.close()

        # Formatar os dados para JSON, convertendo bytes para string
        user_list = []
        for user in users:
            user_data = dict(user)
            user_data["password"] = user_data["password"].decode(
                "utf-8"
            )  # Decodificar hash
            user_list.append(user_data)

        return jsonify(user_list), 200
    except Exception as e:
        logging.error(f"Erro ao recuperar usuários: {e}")
        return jsonify({"message": "Erro ao recuperar usuários"}), 500

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
def user_login():
    """Rota para realizar login de um usuário."""
    data = request.get_json()

    # Extração dos dados enviados no corpo da requisição
    email = data.get("email")
    password = data.get("password")

    # Validação para garantir que email e senha foram enviados
    if not all([email, password]):
        return jsonify({"message": "Email e senha são obrigatórios"}), 400

    try:
        conn = get_db_connection()
        # Consulta para verificar as credenciais (busca o hash da senha)
        user = conn.execute(
            """
            SELECT id, name, phone, email, password
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            # Remove o campo de senha antes de retornar o usuário
            user_data = dict(user)
            user_data.pop("password")  # Remover a senha do retorno
            return jsonify({"message": "Login bem-sucedido", "user": user_data}), 200
        else:
            # Retorna mensagem de credenciais inválidas
            return jsonify({"message": "Credenciais inválidas"}), 401
    except Exception as e:
        logging.error(f"Erro ao realizar login: {e}")
        return jsonify({"message": "Erro ao realizar login"}), 500

    """Rota para realizar login de um usuário."""
    data = request.get_json()

    # Extração dos dados enviados no corpo da requisição
    email = data.get("email")
    password = data.get("password")

    # Validação para garantir que email e senha foram enviados
    if not all([email, password]):
        return jsonify({"message": "Email e senha são obrigatórios"}), 400

    try:
        conn = get_db_connection()
        # Consulta para verificar as credenciais (busca apenas o hash da senha)
        user = conn.execute(
            """
            SELECT id, name, phone, email, password
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        conn.close()

        if user and bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            # Remove o campo de senha antes de retornar o usuário
            user_data = dict(user)
            user_data.pop("password")
            return jsonify({"message": "Login bem-sucedido", "user": user_data}), 200
        else:
            # Retorna mensagem de credenciais inválidas
            return jsonify({"message": "Credenciais inválidas"}), 401
    except Exception as e:
        logging.error(f"Erro ao realizar login: {e}")
        return jsonify({"message": "Erro ao realizar login"}), 500


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
    duration = data.get("duration", 40)  # Valor padrão de 40 minutos
    value = data.get("value", 0.0)

    if not barber or not date or not time:
        return jsonify({"error": "Campos obrigatórios: barber, date, time"}), 400

    try:
        booking_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Formato de data ou hora inválido"}), 400

    new_booking = {
        "id": len(availability.get(barber, [])) + 1,
        "date": date,
        "time": time,
        "duration": duration,
        "service": data.get("service"),
        "value": value,
        "client_name": data.get("name"),
        "client_phone": data.get("phone"),
        "client_email": data.get("email"),
        "barber": barber,
    }

    availability.setdefault(barber, []).append(new_booking)
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
                try:
                    booking_start = datetime.strptime(booking["time"], "%H:%M")
                    # Garantir duração padrão se não estiver definida
                    duration_minutes = booking.get("duration", 40)
                    booking_end = booking_start + timedelta(minutes=duration_minutes)

                    # Verificar se o horário está ocupado
                    if (
                        booking_start <= current_time < booking_end
                        or booking_start < current_time + step <= booking_end
                    ):
                        is_available = False
                        break
                except Exception as e:
                    print(f"Erro ao processar agendamento: {e}")

        if is_available:
            available_times.append(current_time.strftime("%H:%M"))

        current_time += step

    return jsonify({"available_times": available_times})


@app.route("/customer_bookings", methods=["GET"])
def customer_bookings():
    try:
        # Obtém e normaliza os parâmetros da requisição
        client_name = request.args.get("name", "").strip().lower()
        client_phone = "".join(
            filter(str.isdigit, request.args.get("phone", "").strip())
        )

        print(f"Parâmetros normalizados: name={client_name}, phone={client_phone}")

        if not client_name or not client_phone:
            return (
                jsonify({"error": "Os parâmetros 'name' e 'phone' são obrigatórios."}),
                400,
            )

        # Lista para armazenar os agendamentos do cliente
        customer_bookings = []

        # Itera sobre os barbeiros e seus agendamentos
        for barber, bookings in availability.items():
            print(f"Barbeiro: {barber}, Agendamentos: {bookings}")

            # Filtra os agendamentos pelo nome e telefone do cliente
            for booking in bookings:
                print(
                    f"Verificando agendamento: Nome={booking['client_name'].strip().lower()} / "
                    f"Telefone={''.join(filter(str.isdigit, booking['client_phone'].strip()))}"
                )

                if (
                    booking["client_name"].strip().lower() == client_name
                    and "".join(filter(str.isdigit, booking["client_phone"].strip()))
                    == client_phone
                ):
                    print(f"Agendamento encontrado: {booking}")
                    customer_bookings.append(booking)

        # Verifica se algum agendamento foi encontrado
        if not customer_bookings:
            print("Nenhum agendamento encontrado para o cliente.")
            return jsonify([]), 200

        # Retorna os agendamentos encontrados
        return jsonify(customer_bookings), 200

    except Exception as e:
        app.logger.error(f"Erro ao buscar agendamentos: {e}")
        return jsonify({"error": "Erro interno no servidor"}), 500


@app.route("/customer_bookings/<int:booking_id>", methods=["DELETE"])
def delete_customer_booking(booking_id):
    try:
        booking_found = False

        # Itera sobre os barbeiros e seus agendamentos
        for barber, bookings in availability.items():
            for booking in bookings:
                if booking["id"] == booking_id:
                    print(f"Removendo agendamento: {booking}")
                    bookings.remove(booking)
                    booking_found = True
                    break

            if booking_found:
                break

        # Se nenhum agendamento foi encontrado
        if not booking_found:
            print(f"Agendamento com ID {booking_id} não encontrado.")
            return jsonify({"error": "Booking not found"}), 404

        print(f"Agendamento com ID {booking_id} removido com sucesso.")
        return jsonify({"message": "Booking deleted successfully"}), 200

    except Exception as e:
        app.logger.error(f"Erro ao excluir agendamento: {e}")
        return jsonify({"error": "Erro interno no servidor"}), 500


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

    try:
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

        return jsonify(result), 200
    except Exception as e:
        print(
            f"Erro ao buscar caixa diário: {e}"
        )  # Adicione esta linha para logar o erro
        return jsonify({"error": "Internal server error"}), 500


# @app.route("/test-email", methods=["GET"])
# def test_email():
#     try:
#         msg = Message(
#             subject="Teste de E-mail",
#             recipients=["kingbarbeariaapp@outlook.com"],  # Substitua pelo seu e-mail
#             body="Este é um e-mail de teste.",
#         )
#         mail.send(msg)
#         return jsonify({"message": "E-mail de teste enviado com sucesso!"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#     return jsonify(result), 200


if __name__ == "__main__":
    # Remova o modo de depuração e ajuste a porta conforme necessário
    app.run(host="0.0.0.0", port=5000, debug=False)
