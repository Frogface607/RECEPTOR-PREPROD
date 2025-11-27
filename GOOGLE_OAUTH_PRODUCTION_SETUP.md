# 🚀 НАСТРОЙКА GOOGLE OAUTH ДЛЯ ПРОДАКШЕНА (receptorai.pro)

## ✅ ЧТО УЖЕ СДЕЛАНО

- ✅ Google Client ID получен: `747418699923-1bqr6o4c3g4h5dgpj20ijuhmaru4nn3h.apps.googleusercontent.com`
- ✅ Frontend код готов (GoogleAuth компонент)
- ✅ Backend готов (`/api/v1/auth/google` endpoint)

## 🔧 ЧТО НУЖНО СДЕЛАТЬ

### ШАГ 1: Добавить Google Client ID в Vercel (РЕДАКШЕН)

1. Перейди в **Vercel Dashboard**: https://vercel.com/dashboard
2. Выбери проект **receptorai.pro** (или как он называется)
3. Перейди в **Settings** → **Environment Variables**
4. Найди или добавь переменную:
   - **Name**: `REACT_APP_GOOGLE_CLIENT_ID`
   - **Value**: `747418699923-1bqr6o4c3g4h5dgpj20ijuhmaru4nn3h.apps.googleusercontent.com`
   - **Environment**: выбери все три (Production, Preview, Development)
5. Нажми **Save**

### ШАГ 2: Настроить Google Cloud Console для продакшена

1. Перейди в [Google Cloud Console](https://console.cloud.google.com/)
2. Выбери проект где создан OAuth Client ID
3. Перейди **APIs & Services** → **Credentials**
4. Найди OAuth Client ID и открой его для редактирования
5. В разделе **Authorized JavaScript origins** добавь:
   ```
   https://receptorai.pro
   https://www.receptorai.pro
   ```
6. В разделе **Authorized redirect URIs** добавь:
   ```
   https://receptorai.pro
   https://www.receptorai.pro
   ```
7. Нажми **Save**

### ШАГ 3: Задеплоить изменения (если нужно)

После добавления переменной в Vercel:

1. **Вариант А: Автоматический деплой**
   - Vercel автоматически задеплоит после сохранения переменной
   - Подожди 1-2 минуты

2. **Вариант Б: Ручной деплой**
   - Перейди в **Deployments**
   - Нажми **Redeploy** на последнем деплое
   - Или сделай коммит и пуш в GitHub (если настроен автодеплой)

### ШАГ 4: Проверить работу

1. Открой https://receptorai.pro
2. Нажми **"Войти"**
3. Должна появиться красивая кнопка **"Войти через Google"** 🎉
4. При клике должно открыться окно авторизации Google

## 🔍 ПРОВЕРКА

### В Vercel:
- [ ] Переменная `REACT_APP_GOOGLE_CLIENT_ID` добавлена
- [ ] Значение правильное (начинается с `747418699923-...`)
- [ ] Включены все окружения (Production, Preview, Development)
- [ ] Проект задеплоен после добавления переменной

### В Google Cloud Console:
- [ ] В **Authorized JavaScript origins** есть `https://receptorai.pro`
- [ ] В **Authorized redirect URIs** есть `https://receptorai.pro`
- [ ] Если используешь www - добавлен `https://www.receptorai.pro`

### На сайте:
- [ ] Кнопка Google отображается
- [ ] При клике открывается окно авторизации Google
- [ ] После авторизации пользователь входит в систему

## 🐛 ЕСЛИ НЕ РАБОТАЕТ

### Кнопка Google не показывается:
1. Проверь консоль браузера (F12) на ошибки
2. Проверь что переменная `REACT_APP_GOOGLE_CLIENT_ID` в Vercel
3. Убедись что проект перезадеплоен после добавления переменной
4. Проверь что переменная добавлена для **Production** окружения

### Ошибка "Invalid origin":
1. Проверь что в Google Console добавлен `https://receptorai.pro` (с https!)
2. Проверь что нет лишних слешей в конце: `https://receptorai.pro/` ❌

### Ошибка "redirect_uri_mismatch":
1. Проверь что в **Authorized redirect URIs** добавлен `https://receptorai.pro`
2. URL должен точно совпадать (включая https, без слеша в конце)

## 📝 БЫСТРАЯ ССЫЛКА

**Vercel Dashboard**: https://vercel.com/dashboard  
**Google Cloud Console Credentials**: https://console.cloud.google.com/apis/credentials

---

**После настройки Google OAuth будет работать на продакшене!** 🎉

