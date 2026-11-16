"""Факты об общении для бота: короткий текст + что делать + источник.

Собрано 16.11 из исследований (подробности и оговорки — docs/pivot/fakty.md).
reliability: high — рецензируемое исследование; mid — данные сервиса или опрос;
low — направление верное, точные цифры спорные. В боте показывать только high/mid.
"""

import random

FACTS = [
    {
        "id": "questions_liking",
        "text": "Кто задаёт больше вопросов, особенно уточняющих, тот нравится собеседнику сильнее. На быстрых свиданиях такие люди чаще получали второе свидание",
        "tip": "После ответа собеседника спроси «а почему?» или «и как это было?» — это и есть уточняющий вопрос",
        "source": "Huang и др., Journal of Personality and Social Psychology, 2017",
        "url": "https://www.hks.harvard.edu/publications/it-helps-ask-cumulative-benefits-asking-follow-questions",
        "reliability": "high",
    },
    {
        "id": "liking_gap",
        "text": "После разговора люди стабильно недооценивают, насколько понравились собеседнику. Учёные назвали это «разрывом симпатии» — и он держится, сколько бы ни длился разговор, хоть 2 минуты, хоть 45",
        "tip": "Тебе кажется, что разговор прошёл так себе? Скорее всего, собеседнику понравилось больше, чем ты думаешь",
        "source": "Boothby и др., Psychological Science, 2018",
        "url": "https://faculty.wharton.upenn.edu/wp-content/uploads/2020/05/The-Liking-Gap-in-Conversations.pdf",
        "reliability": "high",
    },
    {
        "id": "deep_talk",
        "text": "Глубокие разговоры с незнакомыми людьми оказываются менее неловкими и более приятными, чем ждут участники. 12 экспериментов, больше 1800 человек",
        "tip": "Не бойся спросить что-то настоящее вместо «как дела» — люди интересуются тобой сильнее, чем кажется",
        "source": "Kardas, Kumar, Epley, Journal of Personality and Social Psychology, 2021",
        "url": "https://www.apa.org/news/press/releases/2021/09/deep-conversations-strangers",
        "reliability": "high",
    },
    {
        "id": "self_talk_reward",
        "text": "30–40% речи люди тратят на рассказ о себе. Мозг воспринимает это как награду: в эксперименте участники отказывались от денег, лишь бы поговорить о себе",
        "tip": "Дай человеку рассказать о себе — это приятно ему буквально на уровне мозга",
        "source": "Tamir, Mitchell, PNAS, 2012",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3361411/",
        "reliability": "high",
    },
    {
        "id": "conversation_end",
        "text": "Только около 2% разговоров заканчиваются тогда, когда этого хотят оба. Длину, которую хочет собеседник, люди угадывают с ошибкой больше чем на 60%",
        "tip": "Заканчивай на хорошей ноте, пока интересно, — лучше оставить желание продолжить",
        "source": "Mastroianni и др., PNAS, 2021",
        "url": "https://www.eurekalert.org/news-releases/693716",
        "reliability": "high",
    },
    {
        "id": "fast_friends",
        "text": "36 вопросов с постепенно растущей откровенностью за 45 минут сближают незнакомых людей сильнее, чем обычная болтовня. Это эксперимент Артура Арона 1997 года, позже его прозвали «36 вопросов, чтобы влюбиться»",
        "tip": "Сближает не сам вопрос, а постепенность: от лёгкого к личному",
        "source": "Aron и др., 1997; обзор APS",
        "url": "https://www.psychologicalscience.org/observer/fast-tracking-intimacy",
        "reliability": "high",
    },
    {
        "id": "language_matching",
        "text": "Пары, которые бессознательно подстраиваются под стиль речи друг друга, чаще хотят увидеться снова: 33% против 9% на быстрых свиданиях. В переписке такие пары чаще остаются вместе через 3 месяца: 77% против 54%",
        "tip": "Совпадение стиля нельзя сыграть, но можно заметить: если вы пишете «одинаково», это хороший знак",
        "source": "Ireland, Pennebaker и др., Psychological Science, 2011",
        "url": "https://sites.socsci.uci.edu/~lpearl/courses/readings/IrelandEtAl2011_RelationshipPrediction.pdf",
        "reliability": "high",
    },
    {
        "id": "compliments",
        "text": "Люди делают меньше комплиментов, чем хотели бы, потому что недооценивают, насколько приятно их получать. Получателю важна доброта, а не идеальная формулировка",
        "tip": "Хочешь сказать приятное — скажи. Неловкость только в твоей голове",
        "source": "Zhao, Epley, Journal of Personality and Social Psychology, 2021",
        "url": "https://www.psychologytoday.com/za/blog/ulterior-motives/202110/you-probably-don-t-compliment-other-people-often-enough",
        "reliability": "high",
    },
    {
        "id": "bids",
        "text": "Пары, которые остались вместе через 6 лет, откликались на «заявки на внимание» партнёра в 86% случаев, а распавшиеся — в 33%. Заявка — это любая мелочь вроде «смотри, какая птица»",
        "tip": "Человек скинул мем или фотку? Это заявка на внимание. Ответь — это важнее, чем кажется",
        "source": "Исследования Готтмана (по материалам Gottman Institute)",
        "url": "https://www.gottman.com/blog/turn-toward-instead-of-away/",
        "reliability": "mid",
    },
    {
        "id": "period_text",
        "text": "Короткий ответ с точкой в конце в переписке кажется менее искренним, чем без неё. На бумаге такого эффекта нет. А восклицательный знак, наоборот, добавляет искренности",
        "tip": "«Ок.» звучит холоднее, чем «ок» или «ок!»",
        "source": "Klin, Binghamton University, Computers in Human Behavior, 2016",
        "url": "https://phys.org/news/2015-12-text-messages-period-sincere.html",
        "reliability": "high",
    },
    {
        "id": "emoji_dates",
        "text": "Те, кто чаще ставит эмодзи в переписке, в среднем чаще ходят на свидания. Оптимум по ощущениям людей — не больше трёх эмодзи в сообщении",
        "tip": "Эмодзи передают тон, которого нет в тексте. Но больше трёх подряд — уже перебор",
        "source": "Gesselman, Ta, Garcia, PLOS One, 2019 (корреляция, не причина)",
        "url": "https://www.psypost.org/more-frequent-emoji-use-linked-to-more-first-dates-and-more-sexual-activity-study-finds/",
        "reliability": "mid",
    },
    {
        "id": "first_message_profile",
        "text": "Первое сообщение, которое опирается на анкету или интересы человека, получает ответ заметно чаще, чем «привет». Комплименты внешности вроде «красивая» работают хуже",
        "tip": "Зацепись за что-то из анкеты: «вижу, ты любишь…»",
        "source": "OkCupid, анализ 500 000 первых сообщений, 2009",
        "url": "https://gwern.net/doc/psychology/okcupid/exactlywhattosayinafirstmessage.html",
        "reliability": "mid",
    },
    {
        "id": "first_message_hinge",
        "text": "Лучше всего отвечают на первые сообщения, где есть личный вопрос или предложение конкретного плана",
        "tip": "Вопрос про человека или «давай в субботу…» сильнее, чем «как дела»",
        "source": "Hinge, внутренние данные (по прессе)",
        "url": "https://www.ibtimes.com/best-opening-line-dating-apps-hinge-analyzed-100-responses-its-not-hey-whats-2112058",
        "reliability": "mid",
    },
    {
        "id": "text_after_date",
        "text": "Написать после первого свидания лучше всего на следующее утро. Слишком долгое ожидание не делает тебя «ценнее» — оно выглядит как ненадёжность",
        "tip": "Игра «подожду три дня» не работает. Напиши утром",
        "source": "Teichmann и др., Journal of Social and Personal Relationships, 2026",
        "url": "https://www.psypost.org/psychology-researchers-have-determined-the-best-time-to-text-after-a-first-date/",
        "reliability": "mid",
    },
    {
        "id": "friend_hours",
        "text": "Чтобы из знакомого стать другом, нужно около 50 часов общения, до хорошего друга — около 90, до близкого — больше 200",
        "tip": "Дружба — это время. Позвать на ещё одну встречу — нормально",
        "source": "Jeffrey Hall, Journal of Social and Personal Relationships, 2018",
        "url": "https://www.psychologytoday.com/us/blog/brain-waves/201803/how-do-you-make-or-maintain-friends-put-in-the-time",
        "reliability": "high",
    },
    {
        "id": "dunbar",
        "text": "Число Данбара: одновременно человек поддерживает около 150 значимых связей, около 50 хороших друзей и примерно 5 самых близких",
        "tip": "Самых близких всегда мало — и это нормально",
        "source": "Robin Dunbar",
        "url": "https://www.bustle.com/p/how-long-does-it-take-to-make-friends-scientists-actually-tallied-it-up-heres-what-they-said-8724116",
        "reliability": "mid",
    },
    {
        "id": "mehrabian_myth",
        "text": "Миф: «93% общения — невербалика». Правило 7-38-55 Мехрабиана относится только к случаю, когда слова противоречат тону, и проверялось на отдельных словах, а не на живых разговорах. Сам автор против того, чтобы распространять его на всё общение",
        "tip": "Слова важны. Особенно в переписке, где ничего, кроме слов, нет",
        "source": "Wikipedia: Albert Mehrabian; Big Think",
        "url": "https://bigthink.com/the-learning-curve/the-7-38-55-rule-debunking-the-golden-ratio-of-conversation",
        "reliability": "high",
    },
    {
        "id": "ghosting",
        "text": "Гостинг — обычное дело: по академическому опросу, около двух третей людей хоть раз пропадали сами и примерно столько же пропадали из их жизни",
        "tip": "Не ответили — чаще всего дело не в тебе",
        "source": "Koessler и др.; Leckfor, Wood, 2023 (обзор MDPI)",
        "url": "https://www.mdpi.com/2673-8392/4/1/4",
        "reliability": "mid",
    },
    {
        "id": "laughter",
        "text": "Когда разговаривают незнакомые парень и девушка, смех звучит особенно часто. Девушки смеются в среднем немного больше, а парни чаще смешат",
        "tip": "Смех в разговоре — хороший сигнал, что всё идёт хорошо",
        "source": "Обзоры исследований смеха (Provine и др.)",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10480874/",
        "reliability": "low",
    },
    {
        "id": "voice_messages_ru",
        "text": "Голосовые в России получают 61% людей, а отправляют только 44%",
        "tip": "Не все любят голосовые: спроси, удобно ли человеку их слушать",
        "source": "ВЦИОМ",
        "url": "https://wciom.ru/analytical-reviews/analiticheskii-obzor/golosovye-soobshchenija-pochemu-by-i-net",
        "reliability": "mid",
    },
    {
        "id": "loneliness_young",
        "text": "Молодые чувствуют себя одинокими чаще пожилых: в Англии 31% людей 16–29 лет одиноки хотя бы иногда, против 16% среди тех, кому за 70",
        "tip": "Если тебе одиноко — ты точно не один. Многие рядом чувствуют то же самое",
        "source": "ONS (Великобритания)",
        "url": "https://www.scandinaviastandard.com/t-gen-z-loneliness-80-percent-baby-boomers-45-percent/",
        "reliability": "mid",
    },
]


def for_bot():
    """Только надёжные факты (high/mid)."""
    return [f for f in FACTS if f["reliability"] in ("high", "mid")]


def random_fact(exclude: set[str] | None = None):
    pool = [f for f in for_bot() if not exclude or f["id"] not in exclude]
    return random.choice(pool or for_bot())


def render(fact) -> str:
    """Факт для сообщения бота (HTML)."""
    return f"🧠 <b>Факт</b>\n\n{fact['text']}\n\n💡 {fact['tip']}\n\n<i>{fact['source']}</i>"
