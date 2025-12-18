FROM node:18-alpine

WORKDIR /app

# تثبيت التبعيات
COPY package*.json ./
RUN npm ci --only=production

# نسخ الأكواد
COPY . .

# إنشاء المجلدات
RUN mkdir -p data exports logs backups

# تعيين المستخدم غير الجذري
USER node

# فتح المنفذ
EXPOSE 3000

# أمر التشغيل
CMD ["npm", "start"]
