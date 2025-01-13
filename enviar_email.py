import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

email_de = "wethcommerce@gmail.com"
email_para = "mawetepascoal5@gmail.com"
senha = "ctwz khlo pdbu znvg"

"""
email_de = "mylespascoal@gmail.com"
email_para = "mawetepascoal5@gmail.com"
senha = "s z f r c k s x t n q s w i r r
"""

mensagem = MIMEMultipart()
mensagem["From"] = email_de
mensagem["To"] = email_para
mensagem["Subject"] = "Solicitação de Confirmação de Identidade"



corpo = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            padding: 10px 0;
            background-color: #4CAF50;
            color: white;
            border-radius: 8px 8px 0 0;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .body {
            padding: 20px;
            text-align: center;
            color: #333;
        }
        .body p {
            font-size: 18px;
            margin: 10px 0;
        }
        .code {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            padding: 10px;
            font-size: 12px;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>Confirmação de Identidade</h1>
        </div>
        <div class="body">
            <p>Olá,</p>
            <p>Estamos enviando este e-mail para confirmar sua identidade.</p>
            <p>O seu código de verificação é:</p>
            <div class="code">104358</div>
            <p>Por favor, insira este código no campo indicado para continuar.</p>
        </div>
        <div class="footer">
            <p>Se você não solicitou esta verificação, ignore este e-mail.</p>
            <p>&copy; 2025 Sua Empresa. Todos os direitos reservados.</p>
        </div>
    </div>
</body>
</html>
"""
mensagem.attach(MIMEText(corpo, "html"))
try:
    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    servidor.login(email_de, senha)
    servidor.sendmail(email_de, email_para, mensagem.as_string())
    servidor.close()
    print("E-mail enviado com sucesso!")
except Exception as e:
    print(f"Falha ao enviar o e-mail: {e}")
