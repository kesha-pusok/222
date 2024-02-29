import os
import json
import requests as rq
import pandas as pd
import time
import sys, traceback
import keys as keys

from requests.auth import HTTPBasicAuth
from datetime import datetime

probel = '____________________________________'
pas = HTTPBasicAuth(keys.access_key,keys.secret_key)

#блок отвечает за заполнение отчёта - получает уведомление и вносит его в текстовый файл. (готов)
def add_print (text) :
    file = open("log_bot.txt", "a+")  # открываем файл для создания отчёта по работе бота
    file.write(probel + '\n')
    file.write(str(datetime.now()) + '   ' + text + '\n')
    file.close()


#блок отвечает за формирование нового ордера, получает входные данные( цена, обьём, направление, и выбор( лимит или маркет). Обрабатывает возможные ошибки и возвращает ответ
#сервера в виде json (готов)
def order_plus (price, volume, direction, choice):
    try:
        if choice == 'limit':
            param = {'symbol': keys.symbol_bot, 'side': direction, 'type': choice, 'quantity': str(volume), 'price': str(price), 'strictValidate': 'false'}
        else:
            param = {'symbol': keys.symbol_bot, 'side': direction, 'type': choice, 'quantity': str(volume),
                 'strictValidate': 'false'}
        i = 10
        while i > -1:
            m = rq.post(keys.url+keys.order_plus, data=param, auth=pas).json()
            if 'error' in m:
                text = 'Запрос с параметрами '+str(param)+'вернул ошибку'+'\n'+str(m['error']) +'\n'+ 'Пробуем повторитьзапрос - осталось '+ str(i) +' попыток' +'\n'
                add_print(text)
                i -= 1
                time.sleep(5)
                continue
            else:
                return m
                break
        text ='Попытка открыть ордер с параметрами '+ str(param) +'\n'+'окончилась неудачей. Бот будет остановленн'
        add_print(text)
        sys.exit(0)
    except BaseException as ex:
        if ex.code == 0:
            os._exit(0)
        a = type(ex)
        c = ex.args
        text ='Бот остановленн из за ошибки  ' + str(a) + '  ' + str(c) + '\n' + str(
            traceback.extract_stack()) + '\n' + str(datetime.now()) + '\n'
        add_print(text)
        sys.exit(1)
        os.exit(1)

#начальный блок. Формирование таблицы с данными  и первичное размещение ордеров. (готов) + Добавленны в таблицу 3 зоны для возмодности добваоения ликвидности.
def start_bot():
    try:
        sdelka_setka = pd.DataFrame({'id': ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
                                            '0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
                                     'by_sell': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                     'kas_quantities': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                     'price_sdelka': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                      0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                     'usdt_quantities': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                         0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'zona': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})
        i = 10# получаем список всех активов с баллансами
        while i > -1:
            m = rq.get(keys.url+keys.all_balances, auth=pas).json()
            if 'error' in m:
                text = 'Запрос списка активных баллансов вернул ошибку' + '\n' + str(
                    m['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(i) + ' попыток' + '\n'
                add_print(text)
                i -= 1
                time.sleep(5)
                continue
            else:
                m_pd = pd.DataFrame(m)
                break
        if i == -1:
            text = 'Попыток больше нет - останавливаем бот'
            add_print(text)
            sys.exit(0)

        # узнаём сколько всего у нас тезера
        i = 0
        while i < m_pd.shape[0]:
            if m_pd.iloc[i]['asset'] == 'USDT':
                summ_usdt = float(m_pd.iloc[i]['available'])
                break
            i += 1

        #Проверка на минимальный балланс
        if summ_usdt < 5:
            add_print('Слишком маленький балланс - останавливаем бот')
            sys.exit(0)

        i = 10#узнаём текущую цену Kaspa
        while i > -1:
            m = rq.get(keys.url + keys.statictic_kas_usdt, auth=pas).json()
            if 'error' in m:
                text = 'Запрос информации о торговой паре вернул ошибку' + '\n' + str(
                    m['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(i) + ' попыток' + '\n'
                add_print(text)
                i -= 1
                time.sleep(5)
                continue
            else:
                kas_price = float(m["bestAsk"])
                break
        if i == -1:
            text = 'Попыток больше нет - останавливаем бот'
            add_print(text)
            sys.exit(0)

        #получаем сколько всего монет мы можем купить (оставляем в запасе около 2 монеты на погрешност, чтобы впоследствии не лезли ошибки из за нехватки монет)
        summ_kas = summ_usdt/kas_price
        first_order = int(summ_kas/2)

        #Первичная покупка монет
        m = order_plus(0,first_order,'buy','market')
        text = 'Первично купленно (учитывая запас в 1 монету) ' + str(first_order) + ' монет по цене -' + str(m['numberprice'])
        add_print(text)

        #Заполняем нулевой ордер - он будет на 10 позиции
        price_first = m['numberprice']
        value_one_order = int((float(m['quantity'])-1)/10)#вычитаем 1 монету - запас
        sdelka_setka.loc[10] = ['0', 3, value_one_order, float(price_first), 0, 0]


        #создаём ордера на продажу (делаем сразу всё ранжированно для удобства при просмотре таблицы данных,
        #цена будет уменьшаться снизу вверх
        i=0
        while i<10:
            price_order = float(price_first)*keys.setka_factor_sell[i]
            m=order_plus(price_order,value_one_order,'sell','limit')
            text = 'Sell ордер по цене '+ str(m['numberprice']) + ' открыт'
            add_print(text)
            if i < 3:
                sdelka_setka.loc[i] = [m['userProvidedId'], 2, float(m['quantity']),m['numberprice'], m['remainTotal'], 1]
            else:
                sdelka_setka.loc[i] = [m['userProvidedId'], 2, float(m['quantity']), m['numberprice'], m['remainTotal'],
                                       0]
            i+=1

        #создаём ордера на покупку
        i = 0
        while i < 10:
            price_order = float(price_first) * keys.setka_factor_buy[i]
            m = order_plus(price_order, value_one_order, 'buy', 'limit')
            text = 'Sell ордер по цене ' + str(m['numberprice']) + ' открыт'
            add_print(text)
            if i < 7:
                sdelka_setka.loc[i+11] = [m['userProvidedId'], 1, float(m['quantity']), m['numberprice'], m['remainTotal'],0]
            else:
                sdelka_setka.loc[i + 11] = [m['userProvidedId'], 1, float(m['quantity']), m['numberprice'], m['remainTotal'], -1]
            i += 1

        #Записываем таблицу с данными
        sdelka_setka.to_csv('sdelka_setka.cvs')
    except BaseException as ex:
        if ex.code == 0:
            os._exit(0)
        a = type(ex)
        c = ex.args
        text ='Бот остановленн из за ошибки  ' + str(a) + '  ' + str(c) + '\n' + str(
            traceback.extract_stack()) + '\n' + str(datetime.now()) + '\n'
        add_print(text)
        sys.exit(1)
        os.exit(1)

#основной блок работы бота
def bot_run():
    try:
        while True:
            setca = pd.read_csv('sdelka_setka.cvs')
            setca = setca.iloc[:, 1:]  # считали значение из файла с ордерами + убрали ненужный столбец с номерами

            param = {'symbol': keys.symbol_bot, 'status': 'active', 'limit': 30, 'skip': 0}
            i = 10 #Считываем все открытые ордера
            while i > -1:
                m = rq.get(keys.url + keys.url_myspotorder, data=param, auth=pas).json()
                if 'error' in m:
                    text = 'Запрос с параметрами ' + str(param) + 'вернул ошибку' + '\n' + str(
                        m['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(i) + ' попыток' + '\n'
                    add_print(text)
                    i -= 1
                    time.sleep(5)
                    continue
                else:
                    break
            if i == -1:
                text = 'Попытка открыть ордер с параметрами ' + str(param) + '\n' + 'окончилась неудачей. Бот будет остановленн'
                add_print(text)
                sys.exit(0)

            #убираем ненужнее и переводим в пандас
            activ_order =pd.DataFrame(m)
            activ_order.drop(['id','market','type','executedQuantity','remainQuantity','remainTotalWithFee',
                           'lastTradeAt','status','isActive','createdAt','updatedAt'],axis=1,inplace=True)

            i = 10  # узнаём текущую цену Kaspa
            while i > -1:
                m = rq.get(keys.url + keys.statictic_kas_usdt, auth=pas).json()
                if 'error' in m:
                    text = 'Запрос информации о торговой паре вернул ошибку' + '\n' + str(
                        m['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(i) + ' попыток' + '\n'
                    add_print(text)
                    i -= 1
                    time.sleep(5)
                    continue
                else:
                    tsena = float(m["bestAsk"])
                    break
            if i == -1:
                text = 'Попыток больше нет - останавливаем бот'
                add_print(text)
                sys.exit(0)

            activ_order_index = activ_order.shape[0]
            setca_index = setca.shape[0]

            #проверка есть ли исполненные ордера, если нет пропускаем цикл  - ждём 15 минут и заново
            if activ_order_index == setca.shape[0] - 1:
                add_print('Исполненных ордеров нет, ожидание 15 мин.')
                print('нет ордеров')
                time.sleep(900)
                continue
            #Если есть делаем подготовку
            else:
                i = 0
                spisok_id =[]
                side_for_id = []
                price_id = []
                volum_id = []
                zona_id =[]
                while i<setca.shape[0]:
                    spisok_id.append('0')
                    side_for_id.append('0')
                    price_id.append('0')
                    volum_id.append('0')
                    zona_id.append('0')

                #spisok_id = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
                 #            '0', '0', '0']
                #side_for_id = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
                #               '0', '0', '0']
                #price_id = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
                #            '0', '0', '0']
                #volum_id = ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
                  #          '0', '0', '0']
                s = 0 #счётчик сколько всего ордеров исполнилось, нулевой ордер считает за исполненный
                max_price = 0
                min_price = 1000000
                #ищем отсутствующие ордера, на выходе получаем три списка - исполненн/нет (1/0), какой был ордер, его прайс
                i = 0
                s = 0
                while i < setca_index:
                    j = 0
                    k = 0



                    while j < activ_order_index:
                        if activ_order.iloc[j]['userProvidedId'] == setca.iloc[i]['id']:
                            spisok_id[i] = 1
                            side_for_id[i] = setca.iloc[i]['by_sell']
                            price_id[i] = setca.iloc[i]['price_sdelka']
                            volum_id[i] = setca.iloc[i]['kas_quantities']
                            zona_id[i] = setca.iloc[i]['zona']
                            k = 1
                            break
                        j += 1
                    if k == 0:
                        spisok_id[i] = 0
                        side_for_id[i] = setca.iloc[i]['by_sell']
                        price_id[i] = setca.iloc[i]['price_sdelka']
                        volum_id[i] = setca.iloc[i]['kas_quantities']
                        zona_id[i] = setca.iloc[i]['zona']

                        if price_id[i] > max_price:
                            max_price = price_id[i]
                        if price_id[i] < min_price:
                            min_price = price_id[i]
                        s += 1
                    i += 1


            #основной блок торговли по вариантам
            #исполнился 1 ордер
            if s < 3:
                print('одинордер')
                text = 'обнаружено исполнение еденичного ордера'
                add_print(text)
                # определяем направление сработавшего ордера
                n = 0
                for ind in spisok_id:
                    t = side_for_id[n]
                    if ind == 0 and t != 3:
                        napravlenie = side_for_id[n]
                        break
                    n += 1
                #Сработал ордер BUY, есть два варианта. Цена ушла ввер выше +1 шаг, или в сетке
                if napravlenie == 1:
                    # продажа по маркету 1 лота + восстановление лота на покупку - вносим изменения
                    if tsena > max_price:
                        m = order_plus(setca.iloc[n]['price_sdelka'], setca.iloc[n]['kas_quantities'], 'sell', 'market')
                        text = 'Маркет ордер на продажу выполненн'
                        add_print(text)
                        time.sleep(10)
                        ml = order_plus(setca.iloc[n]['price_sdelka'], setca.iloc[n]['kas_quantities'], 'buy', 'limit')
                        setca.loc[n] = [ml['userProvidedId'], 1, float(ml['quantity']), ml['numberprice'],
                                        float(ml['remainTotal']), zona_id[n]]
                        setca.to_csv('sdelka_setka.cvs')
                        text = 'Лимитный ордер восстановлен, измененя в данные внесены'
                        add_print(text)
                    #выставляем по индексу 3 лимит на продажу+по исполненному ордеру ставим индекс 3  - вносим изменения
                    else:
                        n3 = side_for_id.index(3)
                        if price_id[n] <= price_id[n3]:#количество купленных монет соответствует 0 ордеру
                            m3 = order_plus(setca.iloc[n3]['price_sdelka'], setca.iloc[n]['kas_quantities'], 'sell', 'limit')
                            text = 'Лимитный ордер на продажу выставленн - цена ' + str(setca.iloc[n3]['price_sdelka']) + ' количество - ' + str(setca.iloc[n]['kas_quantities'])
                            add_print(text)
                            setca.loc[n3] = [m3['userProvidedId'], 2, float(m3['quantity']), m3['numberprice'],
                                         float(m3['remainTotal']), zona_id[n3]]
                            setca.loc[n] = ['0', 3, float(m3['quantity']), price_id[n], 0, zona_id[n]]
                            setca.to_csv('sdelka_setka.cvs')
                            text = 'Нулевой ордер установленн на цену - ' + str(setca.iloc[n]['price_sdelka']) + ', изменения в данные внесены'
                            add_print(text)
                        else:
                            #монет больше чем в 0-м

                            vol = volum_id[n]-volum_id[n3]
                            vol_base = volum_id[n3]
                            spisok = []
                            while vol > 0:
                                i = 0
                                while i < n3:
                                    if volum_id[i] < vol_base:
                                        if vol_base - volum_id[i] <= vol:
                                            spisok.append(side_for_id[i], vol_base - volum_id[i])
                                            vol -= (vol_base - volum_id[i])
                                        else:
                                            spisok.append(spisok_id[i], vol)
                                            vol = 0

                                if vol > 0:
                                    i = 0
                                    while i < n3:
                                        if vol > 0:
                                            spisok[i][1] += 1
                                            vol -= 1
                                        else:
                                            break
                            i = 0
                            while i < n3:
                                if spisok[i][1] > 0:
                                    param_close = {'id': setca.iloc[spisok[i][0]]['id']}
                                    j = 10
                                    while j > -1:
                                        m_cl = rq.post(keys.url + keys.close, data=param_close, auth=pas).json()
                                        if 'error' in m_cl:
                                            text = 'Запрос с параметрами ' + str(param_close) + 'вернул ошибку' + '\n' + str(m_cl['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(
                                                j) + ' попыток' + '\n'
                                            add_print(text)
                                            j -= 1
                                            time.sleep(5)
                                            continue
                                        else:
                                            return m
                                            break
                                    time.sleep(2)
                                    m = order_plus(setca.iloc[i]['price_sdelka'], setca.iloc[i]['kas_quantities'] + spisok[i][1], 'sell', 'limit')
                                    setca.loc[i] = [m['userProvidedId'], 2, float(m['quantity']), m['numberprice'],float(m['remainTotal']),zona_id[i]]
                                    setca.to_csv('sdelka_setka.cvs')
                                    text = 'Sell ордер увеличенн на -'+str(spisok[i][1])
                                    add_print(text)
                            m3 = order_plus(setca.iloc[n3]['price_sdelka'], volum_id[n3], 'sell', 'limit')
                            text = 'Лимитный ордер на продажу выставленн - цена ' + str(setca.iloc[n3]['price_sdelka']) + ' количество - ' + str(volum_id[n3])
                            add_print(text)
                            setca.loc[n3] = [m3['userProvidedId'], 2, float(m3['quantity']), m3['numberprice'],
                                             float(m3['remainTotal']), zona_id[n3]]
                            setca.loc[n] = ['0', 3, float(m3['quantity']), price_id[n], 0, zona_id[n]]
                            setca.to_csv('sdelka_setka.cvs')
                            text = 'Нулевой ордер установленн на цену - ' + str(price_id[n]) + ', изменения в данные внесены'
                            add_print(text)

                #Сработал ордер Sell есть два варианта.Цена ушла вниз ниже -1 шаг, или в сетке
                else:
                    #покупка по маркету 1 лота + восстановление лота на продажу + внести изменения
                    if tsena < min_price:
                        m = order_plus(setca.iloc[n]['price_sdelka'], setca.iloc[n]['kas_quantities'], 'buy', 'market')
                        text = 'Маркет ордер на продажу выполненн'
                        add_print(text)
                        time.sleep(10)
                        ml = order_plus(setca.iloc[n]['price_sdelka'], setca.iloc[n]['kas_quantities'], 'sell', 'limit')
                        setca.loc[n] = [ml['userProvidedId'], 2, float(ml['quantity']), ml['numberprice'],
                                        float(ml['remainTotal']), zona_id[n]]
                        setca.to_csv('sdelka_setka.cvs')
                        text = 'Лимитный ордер восстановлен, измененя в данные внесены'
                        add_print(text)
                    #выставляем по индексу 3 лимит на покупку+по исполненному ордеру ставим индекс 3  - вносим изменения
                    else:
                        n3 = side_for_id.index(3)
                        m3 = order_plus(setca.iloc[n3]['price_sdelka'], setca.iloc[n]['kas_quantities'], 'buy',
                                        'limit')
                        text = 'Лимитный ордер на покупку выставленн - цена ' + str(
                            setca.iloc[n3]['price_sdelka']) + ' количество - ' + str(setca.iloc[n]['kas_quantities'])
                        add_print(text)
                        setca.loc[n3] = [m3['userProvidedId'], 1, float(m3['quantity']), m3['numberprice'],
                                         float(m3['remainTotal']),zona_id[n3]]
                        setca.loc[n] = ['0', 3, float(m3['quantity']), price_id[n], 0, zona_id[n]]
                        setca.to_csv('sdelka_setka.cvs')
                        text = 'Нулевой ордер установленн на цену - ' + str(setca.iloc[n]['price_sdelka']) + ', изменения в данные внесены'
                        add_print(text)

            #исполнилось несколько ордеров
            else:
                print('многоордеров')
                text = 'обнаружено исполнение нескольких ордеров'
                add_print(text)
                i = 0
                summ = 0
                order_oll = 0
                sel = 0
                by = 0
                sm = 0
                sl = 0
                bm = 0
                bl = 0
                #перебираем исполненные ордера и ищем те которые подходят под условия продажи по маркету.
                while i < setca_index:
                    #ордер нулевои - пропуск
                    if side_for_id[i] == 3:
                        i += 1
                        continue
                    if side_for_id[i] == 1 and spisok_id[i] == 0:
                        if tsena > price_id[i-1]:
                            summ -= float(setca.iloc[i]['kas_quantities'])
                            bm += 1
                            order_oll -= 1
                        else:
                            bl += 1
                    if side_for_id[i] == 2 and spisok_id[i] == 0:
                        if tsena < price_id[i+1]:
                            summ += float(setca.iloc[i]['kas_quantities'])
                            sm += 1
                            order_oll += 1
                        else:
                            sl += 1
                    i += 1



                #возможно возникновение 3 вар. Болтается в сеткt или возможны продажи по маркету - либо покупки
                if order_oll != 0:
                    #больше sell ордеров
                    if order_oll > 0:
                        m = order_plus(0, summ, 'buy', 'market')
                        text = 'Исполнен buy маркет ордер на сумму - ' + str(summ)
                        add_print(text)
                        time.sleep(5)
                    #больше buy ордеров
                    elif order_oll < 0:
                        m = order_plus(0, - summ, 'sell', 'market')
                        text = 'Исполнен sell маркет ордер на сумму - ' + str(summ)
                        add_print(text)
                        time.sleep(5)
                elif order_oll == 0:
                        text = 'Позиция качели маркет ордеров нет'
                        add_print(text)

                #блок отвечает за восстановление лимитных ордеров и внесение изменений в таблицу
                sel = sm + bl
                by = bm + sl
                ns = 0
                nb = 0
                i = 0

                while i < setca.shape[0]:
                    if spisok_id[i] == 0:
                        #ставим ордера sell - если есть
                        while ns < sel:
                            m = order_plus(price_id[i], setca.iloc[i]['kas_quantities'], 'sell', 'limit')
                            time.sleep(5)
                            setca.loc[i]=[m['userProvidedId'], 2, float(m['quantity']), m['numberprice'], float(m['remainTotal']), zona_id[i]]
                            setca.to_csv('sdelka_setka.cvs')
                            text = 'Лимитный ордер на продажу выставленн. Цена - ' + str(
                                price_id[i]) + ' ,количество - ' + str(setca.iloc[i]['kas_quantities']) + ' Изменения внесены.'
                            add_print(text)
                            ns += 1
                            i += 1
                        #ставим нулевой ордер
                        if i > 0:
                            z = volum_id[i-1]
                        else:
                            z = volum_id[i]
                        setca.loc[i] = ['0', 3, z, price_id[i],0, zona_id[i]]
                        setca.to_csv('sdelka_setka.cvs')
                        text = 'Нулевой ордер восстановлен. Цена - ' + str(
                            price_id[i]) + ' Изменения внесены.'
                        add_print(text)
                        i += 1
                        #ставим ордера sell если есть
                        while nb < by:
                            m = order_plus(price_id[i], setca.iloc[i]['kas_quantities'], 'buy', 'limit')
                            time.sleep(5)
                            setca.loc[i] = [m['userProvidedId'], 1, float(m['quantity']), m['numberprice'],
                                            float(m['remainTotal']), zona_id[i]]
                            setca.to_csv('sdelka_setka.cvs')
                            text = 'Лимитный ордер на покупку выставленн. Цена - ' + str(
                                price_id[i]) + ' ,количество - ' + str(setca.iloc[i][
                                       'kas_quantities']) + ' Изменения внесены.'
                            add_print(text)
                            nb += 1
                            i += 1
                        break
                    i += 1
            text = 'Итерация выполненна - ожидание 15 минут'
            add_print(text)
            print('итерация выполненна')
            time.sleep(900)

    except BaseException as ex:
        if ex.code == 0:
            os._exit(0)
        a = type(ex)
        c = ex.args
        text ='Бот остановленн из за ошибки  ' + str(a) + '  ' + str(c) + '\n' + str(
            traceback.extract_stack()) + '\n' + str(datetime.now()) + '\n'
        add_print(text)
        sys.exit(1)
        os.exit(1)

def bot_add():
    try:
        i = 10  # узнаём текущую цену Kaspa
        text = 'Проверяем на свободные средства'
        add_print(text)
        while i > -1:
            m = rq.get(keys.url + keys.statictic_kas_usdt, auth=pas).json()
            if 'error' in m:
                text = 'Запрос информации о торговой паре вернул ошибку' + '\n' + str(
                    m['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(i) + ' попыток' + '\n'
                add_print(text)
                i -= 1
                time.sleep(5)
                continue
            else:
                tsena = float(m["bestAsk"])
                break
        if i == -1:
            text = 'Попыток больше нет - останавливаем бот'
            add_print(text)
            sys.exit(0)

        i = 10  # получаем список всех активов с баллансами
        while i > -1:
            m = rq.get(keys.url + keys.all_balances, auth=pas).json()
            if 'error' in m:
                text = 'Запрос списка активных баллансов вернул ошибку' + '\n' + str(
                    m['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(i) + ' попыток' + '\n'
                add_print(text)
                i -= 1
                time.sleep(5)
                continue
            else:
                m_pd = pd.DataFrame(m)
                break
        if i == -1:
            text = 'Попыток больше нет - останавливаем бот'
            add_print(text)
            sys.exit(0)

        # узнаём сколько всего у нас тезера
        i = 0
        while i < m_pd.shape[0]:
            if m_pd.iloc[i]['asset'] == 'USDT':
                summ_usdt = float(m_pd.iloc[i]['available'])
                break
            i += 1
        summ = summ_usdt / tsena
        #проверка на наличие свободных средств
        if summ > 2:
            #меняем сетку и ордера
            text = 'Есть свободные - ' + str(int(summ-1)) + ' монеты. Меняем сетку и ордера'
            add_print(text)
            #здесь стоп - делаем добавление по 3 зонам (смотрим по 0 ордеру)
            summ_o = int(summ-1)
            setca = pd.read_csv('sdelka_setka.cvs')
            setca = setca.iloc[:, 1:]  # считали значение из файла с ордерами + убрали ненужный столбец с номерами
            n_zona = setca.loc[setca['by_sell'] == 3]
            n_zona = n_zona['zona']# нашли значение номера зоны
            #есть 5 вариантов зон
            #if n_zona == 2:
            #if n_zona == 1:
            if n_zona == 0:
                i = 0
                buy_n = 0
                buy_mas =[]
                summ_n = 0

                while i<setca.shape[0]:
                    if setca.iloc[i]['zona'] == 0 and setca.iloc[i]['by_sell'] == 1:
                        buy_n +=1# количество buy ордеров в сетке
                        buy_mas.append([i, setca.iloc[i]['kas_quantities'], 0])#создаётся самсрк с индексами и количеством + рустое место для подсчёта добавления монет
                        summ_n += setca.iloc[i]['kas_quantities']
                    i += 1
                n_sredn = 1 / buy_n
                buy_int = int(summ_o/buy_n)#сколько монет надо добавить всем ордерам
                buy_int_dop = summ_o - buy_int#сколько рсталось монет на добавление
                i=0
                while i < buy_n:# считвем вес элесента - если больше среднего ставим 1, нет - 0. заодно считаем сколько надо прибавить
                    buy_mas[i][2] += buy_int
                    if buy_mas[i][1]/summ_n < n_sredn and buy_int_dop > 0:
                        buy_mas[i][2] += 1
                        buy_int_dop -= 1
                    i += 1
                if buy_int_dop > 0:
                    i=0
                    while i < buy_int_dop:
                        buy_mas[i][2] += 1
                        i += 1
                i=0
                while i < buy_n:
                    param_close = {'id':setca.iloc[buy_mas[i][0]]['id']}
                    j = 10
                    while j > -1:
                        m_cl = rq.post(keys.url + keys.close, data=param_close, auth=pas).json()
                        if 'error' in m_cl:
                            text = 'Запрос с параметрами ' + str(param_close) + 'вернул ошибку' + '\n' + str(m_cl['error']) + '\n' + 'Пробуем повторитьзапрос - осталось ' + str(j) + ' попыток' + '\n'
                            add_print(text)
                            j -= 1
                            time.sleep(5)
                            continue
                        else:
                            return m
                            break
                    time.sleep(2)
                    m = order_plus(setca.iloc[buy_mas[i][0]]['price_sdelka'], setca.iloc[buy_mas[i][0]]['kas_quantities']+buy_int[i][1], 'buy', 'limit')
                    setca.loc[buy_mas[i][0]] = [m['userProvidedId'], 1, float(m['quantity']), m['numberprice'], float(m['remainTotal'])]
                    setca.to_csv('sdelka_setka.cvs')
                    text = 'Лимитный ордер на продажу увеличенн в размере. Цена - ' + str(
                        price_id[i]) + ' ,количество - ' + str(setca.iloc[i]['kas_quantities']) + ' Изменения внесены.'
                    add_print(text)











            #if n_zona == -1:
            #if n_zona == -2:

        else:
            text = 'Средств нет'
            add_print(text)


    except BaseException as ex:
        if ex.code == 0:
            os._exit(0)
        a = type(ex)
        c = ex.args
        text ='Бот остановленн из за ошибки  ' + str(a) + '  ' + str(c) + '\n' + str(
            traceback.extract_stack()) + '\n' + str(datetime.now()) + '\n'
        add_print(text)
        sys.exit(1)
        os.exit(1)
def a():
    x = 0
    while True:
        if os.path.isfile('sdelka_setka.cvs'):
            bot_run()
            time.sleep(900)
            x += 1
        else:
            start_bot()

        if x == 100:
            bot_add()
            x = 0

def p():
    sum =[]
    print(sum)
    sum.append([1,1])
    print(sum)
    sum.append([3,4])
    print(sum)
    print(sum[1][0])
    sum[0][1]=5
    sum[1][0]+=1
    print(sum)


start_bot()
bot_add()
#bot_run()
#a()
#p()