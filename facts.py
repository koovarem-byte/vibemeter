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
    {
        "id": "four_horsemen",
        "text": "Готтман назвал четыре «всадника», которые чаще всего предсказывают расставание: критика личности («ты всегда…»), презрение (сарказм, закатывание глаз), оборона («а сам-то») и стена молчания",
        "tip": "Жалуйся на поступок, а не на человека: «меня задело, что…» вместо «ты всегда…»",
        "source": "Исследования Готтмана; Wikipedia: John Gottman",
        "url": "https://en.wikipedia.com/wiki/John_Gottman",
        "reliability": "mid",
    },
    {
        "id": "five_to_one",
        "text": "У устойчивых пар во время ссоры на одно негативное действие приходится около пяти позитивных: шутка, согласие, тёплое слово. В обычной жизни соотношение у них ещё выше",
        "tip": "Ссориться можно. Важно, чтобы хорошего между вами было в разы больше",
        "source": "Gottman Institute, «The Magic Ratio»",
        "url": "https://www.gottman.com/blog/the-magic-ratio/",
        "reliability": "mid",
    },
    {
        "id": "perpetual_problems",
        "text": "По Готтману, около 69% того, из-за чего ссорятся пары, — вечные проблемы: разница характеров и привычек. Решить их нельзя, но можно научиться о них говорить без войны",
        "tip": "Не каждый спор нужно выиграть. Иногда цель — понять, а не переубедить",
        "source": "Gottman Institute (по пересказам)",
        "url": "https://www.psychologytoday.com/us/blog/social-instincts/202512/why-69-percent-of-couples-conflict-will-never-go-away",
        "reliability": "mid",
    },
    {
        "id": "harsh_startup",
        "text": "Как пройдёт трудный разговор, видно по первым трём минутам. Если начать с упрёка или сарказма, разговор почти всегда заканчивается плохо",
        "tip": "Начни мягко: «мне важно поговорить о…», а не «опять ты…»",
        "source": "Gottman Institute, исследование 130 пар молодожёнов",
        "url": "https://www.gottman.com/blog/the-6-things-that-predict-divorce/",
        "reliability": "mid",
    },
    {
        "id": "good_news",
        "text": "Как ты реагируешь на хорошие новости близкого человека, говорит об отношениях больше, чем поддержка в беде. Пары, где радуются активно и расспрашивают, довольнее отношениями",
        "tip": "Друг похвастался? Не «ну норм», а «ого! как это было? расскажи»",
        "source": "Gable, Reis и др., 2004",
        "url": "https://www.sas.rochester.edu/psy/people/faculty/reis_harry/assets/pdf/GableReisImpettAsher_2004.pdf",
        "reliability": "high",
    },
    {
        "id": "phubbing",
        "text": "Когда партнёр «залипает» в телефон при тебе, это снижает удовлетворённость отношениями — через ссоры из-за телефона. Почти половина опрошенных сталкивались с этим",
        "tip": "Разговор важный? Положи телефон экраном вниз",
        "source": "Roberts, David, Computers in Human Behavior, 2016",
        "url": "https://kellercenter.hankamer.baylor.edu/news/story/2017/partner-phubbing-how-cell-phones-impact-romantic-partnerships",
        "reliability": "high",
    },
    {
        "id": "fight_by_text",
        "text": "Пары, которые выясняют отношения и извиняются в переписке, в среднем менее довольны отношениями. А вот тёплые сообщения связаны с более счастливыми отношениями",
        "tip": "Нежность — в чат. Серьёзный разговор — голосом или вживую",
        "source": "Schade, Sandberg, BYU, 2013 (корреляция)",
        "url": "https://news.byu.edu/news/too-much-texting-can-disconnect-couples-research-finds",
        "reliability": "mid",
    },
    {
        "id": "divorce_denmark",
        "text": "В опросе 2371 недавно разведённого датчанина чаще всего называли нехватку любви и близости (47%) и проблемы в общении (44%). Измену — только 27%",
        "tip": "Чаще всего пары рушит не измена, а то, что люди перестают говорить друг с другом",
        "source": "Journal of Sex & Marital Therapy (Дания)",
        "url": "https://www.yahoo.com/lifestyle/4-most-common-reasons-divorce-165149580.html",
        "reliability": "mid",
    },
    {
        "id": "divorce_russia",
        "text": "Россияне по опросу ВЦИОМ главной причиной разводов называют деньги (46%), потом поведение партнёра — измены, вредные привычки (31%) — и проблемы в общении (23%)",
        "tip": "Про деньги тоже надо уметь говорить — это такой же разговор, как остальные",
        "source": "ВЦИОМ",
        "url": "https://mel.fm/novosti/2715649-vtsiom-pochti-polovina-rossiyan-nazvala-glavnoy-prichinoy-razvodov-denezhnyye-trudnosti",
        "reliability": "mid",
    },
    {
        "id": "active_listening",
        "text": "Когда в ответ пересказывают твою мысль своими словами и уточняют, люди чувствуют себя понятыми сильнее, чем когда им дают совет",
        "tip": "Вместо совета: «то есть тебя больше всего задело, что…?»",
        "source": "Weger и др., International Journal of Listening, 2014",
        "url": "https://reachfamilies.umn.edu/node/5262",
        "reliability": "high",
    },
    {
        "id": "apology",
        "text": "Самая важная часть извинения — признать свою ответственность, на втором месте — предложить исправить. Слабее всего работает «прости меня»",
        "tip": "Не «извини, если обидел», а «я был неправ, что… Давай я…»",
        "source": "Lewicki и др., Ohio State University, 2016",
        "url": "https://news.osu.edu/the-6-elements-of-an-effective-apology-according-to-science/",
        "reliability": "high",
    },
    {
        "id": "gratitude",
        "text": "Благодарность скрепляет отношения: сказанное «спасибо» делает человека в глазах другого теплее, и тот охотнее продолжает общение",
        "tip": "Скажи спасибо за мелочь, которую обычно не замечаешь",
        "source": "Algoe и др., Emotion, 2014; обзор Algoe, 2012",
        "url": "https://pubmed.ncbi.nlm.nih.gov/25111881/",
        "reliability": "high",
    },
    {
        "id": "humblebrag",
        "text": "Скромное хвастовство («ну вот, опять меня повысили, устал») нравится людям меньше, чем честное хвастовство и даже чем жалоба. Его считывают как неискренность",
        "tip": "Хочешь похвастаться — хвастайся прямо. Это честнее и симпатичнее",
        "source": "Sezer, Gino, Norton, Journal of Personality and Social Psychology, 2018",
        "url": "https://www.library.hbs.edu/working-knowledge/humblebragging-is-a-bad-strategy-especially-in-a-job-interview",
        "reliability": "high",
    },
    {
        "id": "spotlight",
        "text": "Эффект прожектора: нам кажется, что наши промахи замечают все. В эксперименте студенты в нелепой футболке думали, что её заметили вдвое больше людей, чем на самом деле",
        "tip": "Ляпнул что-то? Скорее всего, никто кроме тебя этого уже не помнит",
        "source": "Gilovich, Medvec, Savitsky, 2000",
        "url": "https://www.psychologytoday.com/us/blog/between-you-and-me/201311/have-you-fallen-prey-to-the-spotlight-effect",
        "reliability": "high",
    },
    {
        "id": "reach_out",
        "text": "Написать старому другу, с которым давно не общались, — люди ценят это сильно больше, чем ждёт отправитель. 13 экспериментов, почти 6 тысяч участников",
        "tip": "Вспомнил человека — напиши ему прямо сейчас. Даже «привет, вспомнил тебя»",
        "source": "Liu и др., Journal of Personality and Social Psychology, 2022",
        "url": "https://www.psypost.org/2022/08/study-identifies-a-robust-tendency-to-underestimate-how-much-others-appreciate-being-reached-out-to-63627",
        "reliability": "high",
    },
    {
        "id": "unsolicited_advice",
        "text": "Непрошеный совет часто считывают как критику: будто человек сам не справится. Даже от друга",
        "tip": "Прежде чем советовать, спроси: «хочешь совет или просто выговориться?»",
        "source": "Исследования непрошеной помощи (PsyPost; Cambridge Judge, 2021)",
        "url": "https://www.jbs.cam.ac.uk/2021/tainted-suggestions/",
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


def fact_of_day():
    """Один факт на день (по Москве), у всех одинаковый."""
    from datetime import datetime, timedelta, timezone
    pool = for_bot()
    day = datetime.now(timezone(timedelta(hours=3))).date().toordinal()
    return pool[day % len(pool)]
