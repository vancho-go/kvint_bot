import telebot
import cherrypy
import config
import dbbot

WEBHOOK_HOST = config.host_ip
WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

bot = telebot.TeleBot(config.token)

# Наш вебхук-сервер
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

# # Наша стейт машина
# class StateMachine(object):
#     states = ['S_ENTER_SIZE', 'S_ENTER_PAY_TYPE', 'S_SEND_CONFIRM']
    
#     def __init__(self):
#         self.machine = Machine(model=self, states=StateMachine.states, initial='S_ENTER_SIZE')

#         self.machine.add_transition(trigger='', source='', dest='')
#         self.machine.add_transition('size_entered', 'S_ENTER_SIZE', 'S_ENTER_PAY_TYPE')
#         self.machine.add_transition('pay_entered', 'S_ENTER_PAY_TYPE', 'S_SEND_CONFIRM')
#         self.machine.add_transition('confirm_sent', 'S_SEND_CONFIRM', 'S_ENTER_SIZE')

# Начало диалога
@bot.message_handler(commands=["start"])
def cmd_start(message):
    state = dbbot.get_current_state(message.chat.id)
    print(state)
    if state == 'S_ENTER_PAY_TYPE':
        bot.send_message(message.chat.id, "Как вы будете платить? Наличка или безнал?")
    elif state == 'S_SEND_CONFIRM':
        bot.send_message(message.chat.id, "Вы хотите () пиццу, оплата - ()?")
    else:  # Под "остальным" понимаем состояние "0" - начало диалога
        bot.send_message(message.chat.id, "Какую вы хотите пиццу? Большую или маленькую?")
        dbbot.set_state(message.chat.id, 'S_ENTER_SIZE')


# По команде /reset будем сбрасывать состояния, возвращаясь к началу диалога
@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    bot.send_message(message.chat.id, "Какую вы хотите пиццу? Большую или маленькую?")
    dbbot.set_state(message.chat.id, 'S_ENTER_SIZE')


@bot.message_handler(func=lambda message: dbbot.get_current_state(message.chat.id) == 'S_ENTER_SIZE')
def user_entering_size(message):
    if not message.text in ['Большую', 'Маленькую', 'маленькую', 'большую']:
        bot.send_message(message.chat.id, "Что-то не так, попробуй ещё раз!")
        return
    bot.send_message(message.chat.id, "Как вы будете платить? Наличка или безнал?")
    dbbot.set_state(message.chat.id, 'S_ENTER_PAY_TYPE')
    dbbot.set_size(message.chat.id, message.text)


@bot.message_handler(func=lambda message: dbbot.get_current_state(message.chat.id) == 'S_ENTER_PAY_TYPE')
def user_entering_pay_type(message):
    if not message.text in ['Наличка', 'Безнал', 'наличка', 'безнал']:
        bot.send_message(message.chat.id, "Что-то не так, попробуй ещё раз!")
        return
    else:
        dbbot.set_pay_type(message.chat.id, message.text)
        size = dbbot.get_size(message.chat.id)
        pay_type = dbbot.get_pay_type(message.chat.id)
        bot.send_message(message.chat.id, f"Вы хотите: пиццу - {size}, оплата - {pay_type}?")
        dbbot.set_state(message.chat.id, 'S_SEND_CONFIRM')


@bot.message_handler(func=lambda message: dbbot.get_current_state(message.chat.id) == 'S_SEND_CONFIRM')
def user_answering(message):
    if not message.text in ['Да', 'да']:
        bot.send_message(message.chat.id, "Что-то не так, попробуй сначала! Для повторного заказа отправь команду /start")
    else:
        bot.send_message(message.chat.id, "Спасибо за заказ!")
        bot.send_message(message.chat.id, "Для повторного заказа отправь команду /start")
    dbbot.set_state(message.chat.id, 'S_ENTER_SIZE')



# Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
bot.remove_webhook()

# Ставим заново вебхук
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Указываем настройки сервера CherryPy
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

 # Собственно, запуск!
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
