access_key = '6419c0fc914ff3afbff51dc934c1da88'
secret_key = '4484b4f4fc2df0f81fe741316fc9ccb5f03a10b6358cb9f2'
symbol_bot = 'KAS/USDT'
setka_factor_sell = [1.25, 1.215, 1.18, 1.15, 1.12, 1.095, 1.07, 1.05, 1.03, 1.015]
setka_factor_buy = [0.985, 0.97, 0.95, 0.93, 0.905, 0.88, 0.85, 0.82, 0.785, 0.75]
url = 'https://api.xeggex.com/api/v2' #конечная точка апи
order_plus = '/createorder' #создание ордера
statictic_kas_usdt = '/market/getbysymbol/KAS_USDT' #переменная для проверки текущей цены
url_myspotorder = '/getorders' # получение списка ордеров
all_close = '/cancelallorders' # закрытие всех ордеров
all_balances = '/balances' #список всех не нулевых баллансов
stat_price = '/market/getbysymbol/' #переменная для проверки
close = '/cancelorder' #закрыть один ордер