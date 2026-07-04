
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from database import SessionLocal, User, Archive, init_db
from config import TOKEN, ADMIN_ID
from sqlalchemy import func
from template_processor import process_template_image
import io

# States for ConversationHandler
MAIN_MENU, SELECT_MONTH, SELECT_WEEK, SELECT_ACTIVITY, SEND_TEXT, SEND_MEDIA, ADMIN_MENU, ADMIN_SELECT_MONTH, ADMIN_SELECT_WEEK, TEMPLATE_PASSWORD, TEMPLATE_TEXT, TEMPLATE_IMAGE, ADMIN_MANAGE_USERS, ADMIN_ADD_USER_ID, ADMIN_ADD_USER_USERNAME, ADMIN_REMOVE_USER_ID, ADMIN_CHANGE_ROLE_ID, ADMIN_CHANGE_ROLE_NEW_ROLE, REPORTS_MENU, REPORT_SELECT_MONTH, REPORT_SELECT_WEEK = range(21)

# Configuration for template feature
from config import TEMPLATE_PASSWORD_SECRET

# Hijri Months and Weeks
HIJRI_MONTHS = [
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الثانية",
    "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
]
WEEKS = ["الأول", "الثاني", "الثالث", "الرابع"]

ACTIVITY_TYPES = {
    "فعاليات وندوات للمناسبات": ["صور مع الخبر", "فيديو"],
    "اجتماعات ولقاءات": ["صورة مع الخبر"],
    "ورشات": [],
    "دورات": [],
    "نزول ميداني": [],
    "أنشطة الجانب الإعلامي": [],
    "أنشطة أخرى": []
}

# Helper function to get or create user
def get_or_create_user(user_id, username):
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user

# Start command handler
async def start(update: Update, context) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.username
    user = get_or_create_user(user_id, username)

    keyboard = [
        [InlineKeyboardButton("اختيار الشهر الهجري", callback_data=\'main_menu_month\')],
        [InlineKeyboardButton("التقارير الإحصائية", callback_data=\'main_menu_reports\')],
    ]
    if user.role == \'Admin\':
        keyboard.append([InlineKeyboardButton("القولبة والتوثيق", callback_data=\'main_menu_template\')])
        keyboard.append([InlineKeyboardButton("لوحة تحكم المشرف", callback_data=\'main_menu_admin\')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(\'مرحباً بك في بوت المكتبة الإلكترونية للأرشفة والتوثيق!\nالرجاء اختيار أحد الخيارات:\', reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(\'مرحباً بك في بوت المكتبة الإلكترونية للأرشفة والتوثيق!\nالرجاء اختيار أحد الخيارات:\', reply_markup=reply_markup)
    return MAIN_MENU

async def main_menu_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == \'main_menu_month\':
        return await select_month(update, context)
    elif data == \'main_menu_reports\':
        return await reports_menu(update, context)
    elif data == \'main_menu_template\':
        await query.edit_message_text("الرجاء إدخال كلمة المرور للوصول إلى ميزة القولبة والتوثيق:")
        return TEMPLATE_PASSWORD
    elif data == \'main_menu_admin\':
        return await admin_menu(update, context)
    return MAIN_MENU

async def select_month(update: Update, context) -> int:
    keyboard = []
    for month in HIJRI_MONTHS:
        keyboard.append([InlineKeyboardButton(month, callback_data=f\'month_{month}\')])
    keyboard.append([InlineKeyboardButton("العودة للقائمة الرئيسية", callback_data=\'back_to_main\')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("الرجاء اختيار الشهر الهجري:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("الرجاء اختيار الشهر الهجري:", reply_markup=reply_markup)
    return SELECT_MONTH

async def month_selection_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    month = query.data.split(\'_\')[1]
    context.user_data[\'selected_month\'] = month
    return await select_week(update, context)

async def select_week(update: Update, context) -> int:
    keyboard = []
    for week in WEEKS:
        keyboard.append([InlineKeyboardButton(week, callback_data=f\'week_{week}\')])
    keyboard.append([InlineKeyboardButton("العودة لاختيار الشهر", callback_data=\'back_to_month_selection\')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(f"لقد اخترت شهر {context.user_data[\'selected_month\']}. الرجاء اختيار الأسبوع:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"لقد اخترت شهر {context.user_data[\'selected_month\']}. الرجاء اختيار الأسبوع:", reply_markup=reply_markup)
    return SELECT_WEEK

async def week_selection_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    week = query.data.split(\'_\')[1]
    context.user_data[\'selected_week\'] = week
    return await select_activity(update, context)

async def select_activity(update: Update, context) -> int:
    keyboard = []
    for activity_type in ACTIVITY_TYPES.keys():
        keyboard.append([InlineKeyboardButton(activity_type, callback_data=f\'activity_{activity_type}\')])
    keyboard.append([InlineKeyboardButton("العودة لاختيار الأسبوع", callback_data=\'back_to_week_selection\')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(f"لقد اخترت شهر {context.user_data[\'selected_month\']} والأسبوع {context.user_data[\'selected_week\']}. الرجاء اختيار نوع النشاط:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"لقد اخترت شهر {context.user_data[\'selected_month\']} والأسبوع {context.user_data[\'selected_week\']}. الرجاء اختيار نوع النشاط:", reply_markup=reply_markup)
    return SELECT_ACTIVITY

async def activity_selection_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    activity_type = query.data.split(\'_\', 1)[1] # Split only on the first underscore
    context.user_data[\'selected_activity\'] = activity_type
    await query.edit_message_text(f"لقد اخترت النشاط: {activity_type}. يرجى إرسال نص التقرير أو التوثيق:")
    return SEND_TEXT

async def receive_news_text(update: Update, context) -> int:
    context.user_data[\'news_text\'] = update.message.text
    keyboard = [[InlineKeyboardButton("حفظ واعتماد", callback_data=\'save_archive\')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("يرجى إرسال الوسائط (صور/فيديو/PDF) إن وجدت، أو اضغط حفظ:", reply_markup=reply_markup)
    return SEND_MEDIA

async def receive_media(update: Update, context) -> int:
    if update.message.photo:
        file_id = update.message.photo[-1].file_id # Get the highest resolution photo
        content_type = "صور مع الخبر"
    elif update.message.video:
        file_id = update.message.video.file_id
        content_type = "فيديو"
    elif update.message.document:
        file_id = update.message.document.file_id
        content_type = "ملف (PDF/أخرى)"
    else:
        await update.message.reply_text("نوع الوسائط غير مدعوم. يرجى إرسال صورة أو فيديو أو ملف PDF.")
        return SEND_MEDIA

    context.user_data[\'file_telegram_id\'] = file_id
    context.user_data[\'content_type\'] = content_type

    keyboard = [[InlineKeyboardButton("حفظ واعتماد", callback_data=\'save_archive\')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"تم استلام الوسائط ({content_type}). اضغط حفظ واعتماد لإنهاء الأرشفة.", reply_markup=reply_markup)
    return SEND_MEDIA

async def save_archive(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    username = update.effective_user.username
    user = get_or_create_user(user_id, username)

    selected_month = context.user_data.get(\'selected_month\')
    selected_week = context.user_data.get(\'selected_week\')
    selected_activity = context.user_data.get(\'selected_activity\')
    news_text = context.user_data.get(\'news_text\')
    file_telegram_id = context.user_data.get(\'file_telegram_id\')
    content_type = context.user_data.get(\'content_type\', \'نص فقط\')

    db = SessionLocal()
    try:
        new_archive = Archive(
            user_id=user.user_id,
            hijri_month=selected_month,
            week_number=selected_week,
            activity_type=selected_activity,
            content_type=content_type,
            news_text=news_text,
            file_telegram_id=file_telegram_id
        )
        db.add(new_archive)
        db.commit()
        db.refresh(new_archive)

        await query.edit_message_text("تم حفظ الأرشفة بنجاح!")

        # Notify admins
        admin_message = f"قام المستخدم [{user.username}] بأرشفة [{selected_activity}] لشهر [{selected_month}] الأسبوع [{selected_week}]."
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

    except Exception as e:
        await query.edit_message_text(f"حدث خطأ أثناء حفظ الأرشفة: {e}")
        db.rollback()
    finally:
        db.close()

    context.user_data.clear() # Clear user data after archiving
    return ConversationHandler.END # End the conversation for now, user can start again

async def reports_menu(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("تقرير إحصائي أسبوعي", callback_data=\'report_weekly_select_month\')],
        [InlineKeyboardButton("تقرير إحصائي شهري", callback_data=\'report_monthly_select_month\')],
        [InlineKeyboardButton("العودة للقائمة الرئيسية", callback_data=\'back_to_main\')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("الرجاء اختيار نوع التقرير:", reply_markup=reply_markup)
    return REPORTS_MENU

async def report_select_month(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    report_type = query.data.split(\'_\')[1] # weekly or monthly
    context.user_data[\'report_type\'] = report_type

    keyboard = []
    for month in HIJRI_MONTHS:
        keyboard.append([InlineKeyboardButton(month, callback_data=f\'report_month_{month}\')])
    keyboard.append([InlineKeyboardButton("العودة لتقارير الإحصائيات", callback_data=\'back_to_reports_menu\')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("الرجاء اختيار الشهر للتقرير:", reply_markup=reply_markup)
    return REPORT_SELECT_MONTH

async def report_month_selection_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    month = query.data.split(\'_\')[2]
    context.user_data[\'report_selected_month\'] = month

    report_type = context.user_data.get(\'report_type\')
    if report_type == \'weekly\':
        return await report_select_week(update, context)
    elif report_type == \'monthly\':
        return await generate_monthly_report(update, context)

async def report_select_week(update: Update, context) -> int:
    keyboard = []
    for week in WEEKS:
        keyboard.append([InlineKeyboardButton(week, callback_data=f\'report_week_{week}\')])
    keyboard.append([InlineKeyboardButton("العودة لاختيار الشهر", callback_data=\'back_to_report_month_selection\')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(f"لقد اخترت شهر {context.user_data[\'report_selected_month\']}. الرجاء اختيار الأسبوع للتقرير:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"لقد اخترت شهر {context.user_data[\'report_selected_month\']}. الرجاء اختيار الأسبوع للتقرير:", reply_markup=reply_markup)
    return REPORT_SELECT_WEEK

async def report_week_selection_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    week = query.data.split(\'_\')[2]
    context.user_data[\'report_selected_week\'] = week
    return await generate_weekly_report(update, context)

async def generate_weekly_report(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()

    selected_month = context.user_data.get(\'report_selected_month\')
    selected_week = context.user_data.get(\'report_selected_week\')

    db = SessionLocal()
    report_data = db.query(Archive.activity_type, func.count(Archive.activity_type)).filter(
        Archive.hijri_month == selected_month,
        Archive.week_number == selected_week
    ).group_by(Archive.activity_type).all()
    db.close()

    report_text = f"📊 إحصائية الأسبوع [{selected_week}] لشهر [{selected_month}]:\n"
    total_activities = 0
    for activity_type, count in report_data:
        report_text += f"{activity_type}: ({count} أنشطة)\n"
        total_activities += count
    report_text += f"إجمالي المواد المؤرشفة: ({total_activities} أنشطة)"

    await query.edit_message_text(report_text)
    context.user_data.clear()
    return MAIN_MENU

async def generate_monthly_report(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()

    selected_month = context.user_data.get(\'report_selected_month\')

    db = SessionLocal()
    monthly_report_data = {}
    for week in WEEKS:
        weekly_data = db.query(Archive.activity_type, func.count(Archive.activity_type)).filter(
            Archive.hijri_month == selected_month,
            Archive.week_number == week
        ).group_by(Archive.activity_type).all()
        monthly_report_data[week] = {activity: count for activity, count in weekly_data}
    db.close()

    report_text = f"📊 إحصائية شهر [{selected_month}] الشهرية:\n\n"
    for week in WEEKS:
        report_text += f"الأسبوع [{week}]:\n"
        total_week_activities = 0
        if monthly_report_data[week]:
            for activity_type, count in monthly_report_data[week].items():
                report_text += f"  {activity_type}: ({count} أنشطة)\n"
                total_week_activities += count
        else:
            report_text += "  لا توجد أنشطة هذا الأسبوع.\n"
        report_text += f"  إجمالي الأنشطة للأسبوع: ({total_week_activities} أنشطة)\n\n"

    await query.edit_message_text(report_text)
    context.user_data.clear()
    return MAIN_MENU

async def admin_menu(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user = get_or_create_user(user_id, update.effective_user.username)

    if user.role != \'Admin\':
        await query.edit_message_text("ليس لديك صلاحية الوصول إلى لوحة تحكم المشرف.")
        return MAIN_MENU

    keyboard = [
        [InlineKeyboardButton("استعراض الأرشيف", callback_data=\'admin_view_archive\')],
        [InlineKeyboardButton("إدارة المستخدمين", callback_data=\'admin_manage_users\')],
        [InlineKeyboardButton("العودة للقائمة الرئيسية", callback_data=\'back_to_main\')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("لوحة تحكم المشرف:\nالرجاء اختيار أحد الخيارات:", reply_markup=reply_markup)
    return ADMIN_MENU

async def admin_view_archive_month(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    for month in HIJRI_MONTHS:
        keyboard.append([InlineKeyboardButton(month, callback_data=f\'admin_month_{month}\')])
    keyboard.append([InlineKeyboardButton("العودة للوحة تحكم المشرف", callback_data=\'back_to_admin_menu\')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("الرجاء اختيار الشهر لاستعراض الأرشيف:", reply_markup=reply_markup)
    return ADMIN_SELECT_MONTH

async def admin_month_selection_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    month = query.data.split(\'_\')[2]
    context.user_data[\'admin_selected_month\'] = month
    return await admin_view_archive_week(update, context)

async def admin_view_archive_week(update: Update, context) -> int:
    keyboard = []
    for week in WEEKS:
        keyboard.append([InlineKeyboardButton(week, callback_data=f\'admin_week_{week}\')])
    keyboard.append([InlineKeyboardButton("العودة لاختيار الشهر", callback_data=\'back_to_admin_month_selection\')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(f"لقد اخترت شهر {context.user_data[\'admin_selected_month\']}. الرجاء اختيار الأسبوع لاستعراض الأرشيف:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"لقد اخترت شهر {context.user_data[\'admin_selected_month\']}. الرجاء اختيار الأسبوع لاستعراض الأرشيف:", reply_markup=reply_markup)
    return ADMIN_SELECT_WEEK

async def admin_week_selection_handler(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    week = query.data.split(\'_\')[2]
    context.user_data[\'admin_selected_week\'] = week
    return await send_archive_report(update, context)

async def send_archive_report(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()

    selected_month = context.user_data.get(\'admin_selected_month\')
    selected_week = context.user_data.get(\'admin_selected_week\')

    db = SessionLocal()
    archives = db.query(Archive).filter(
        Archive.hijri_month == selected_month,
        Archive.week_number == selected_week
    ).all()
    db.close()

    if not archives:
        await query.edit_message_text(f"لا توجد أرشيفات لشهر {selected_month} الأسبوع {selected_week}.")
        return ADMIN_MENU

    report_text = f"تقرير الأرشيف لشهر {selected_month} الأسبوع {selected_week}:\n\n"
    for archive in archives:
        report_text += f"نوع النشاط: {archive.activity_type}\n"
        report_text += f"المحتوى: {archive.news_text}\n"
        if archive.file_telegram_id:
            # Re-send files using file_telegram_id
            if archive.content_type == "صور مع الخبر":
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=archive.file_telegram_id)
            elif archive.content_type == "فيديو":
                await context.bot.send_video(chat_id=query.message.chat_id, video=archive.file_telegram_id)
            elif archive.content_type == "ملف (PDF/أخرى)":
                await context.bot.send_document(chat_id=query.message.chat_id, document=archive.file_telegram_id)
            report_text += f"تم إرسال الوسائط أعلاه.\n"
        report_text += "--------------------\n"

    await query.edit_message_text(report_text)
    return ADMIN_MENU

async def admin_manage_users(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    user_list_text = "قائمة المستخدمين:\n"
    for user in users:
        user_list_text += f"ID: {user.user_id}, Username: {user.username}, Role: {user.role}\n"

    keyboard = [
        [InlineKeyboardButton("إضافة مستخدم", callback_data=\'admin_add_user\')],
        [InlineKeyboardButton("حذف مستخدم", callback_data=\'admin_remove_user\')],
        [InlineKeyboardButton("تغيير صلاحية مستخدم", callback_data=\'admin_change_role\')],
        [InlineKeyboardButton("العودة للوحة تحكم المشرف", callback_data=\'back_to_admin_menu\')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(user_list_text + "\nالرجاء اختيار إجراء:", reply_markup=reply_markup)
    return ADMIN_MANAGE_USERS

async def admin_add_user(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إرسال معرف المستخدم (User ID) لإضافته:")
    return ADMIN_ADD_USER_ID

async def admin_receive_add_user_id(update: Update, context) -> int:
    try:
        user_id = int(update.message.text)
        context.user_data[\'new_user_id\'] = user_id
        await update.message.reply_text("الرجاء إرسال اسم المستخدم (Username) للمستخدم الجديد:")
        return ADMIN_ADD_USER_USERNAME
    except ValueError:
        await update.message.reply_text("معرف المستخدم غير صالح. الرجاء إرسال رقم صحيح.")
        return ADMIN_ADD_USER_ID

async def admin_receive_add_user_username(update: Update, context) -> int:
    username = update.message.text
    user_id = context.user_data.get(\'new_user_id\')

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.user_id == user_id).first()
        if existing_user:
            await update.message.reply_text(f"المستخدم بمعرف {user_id} موجود بالفعل.")
        else:
            new_user = User(user_id=user_id, username=username, role=\'User\')
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            await update.message.reply_text(f"تم إضافة المستخدم {username} (ID: {user_id}) بنجاح كـ User.")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء إضافة المستخدم: {e}")
        db.rollback()
    finally:
        db.close()

    return await admin_menu(update, context) # Go back to admin menu

async def admin_remove_user(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إرسال معرف المستخدم (User ID) لحذفه:")
    return ADMIN_REMOVE_USER_ID

async def admin_receive_remove_user_id(update: Update, context) -> int:
    try:
        user_id = int(update.message.text)
        db = SessionLocal()
        user_to_remove = db.query(User).filter(User.user_id == user_id).first()
        if user_to_remove:
            db.delete(user_to_remove)
            db.commit()
            await update.message.reply_text(f"تم حذف المستخدم بمعرف {user_id} بنجاح.")
        else:
            await update.message.reply_text(f"المستخدم بمعرف {user_id} غير موجود.")
    except ValueError:
        await update.message.reply_text("معرف المستخدم غير صالح. الرجاء إرسال رقم صحيح.")
        db.rollback()
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء حذف المستخدم: {e}")
        db.rollback()
    finally:
        db.close()

    return await admin_menu(update, context)

async def admin_change_role(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إرسال معرف المستخدم (User ID) لتغيير صلاحيته:")
    return ADMIN_CHANGE_ROLE_ID

async def admin_receive_change_role_id(update: Update, context) -> int:
    try:
        user_id = int(update.message.text)
        context.user_data[\'user_to_change_role\'] = user_id
        keyboard = [
            [InlineKeyboardButton("Admin", callback_data=\'change_role_Admin\')],
            [InlineKeyboardButton("User", callback_data=\'change_role_User\')],
            [InlineKeyboardButton("إلغاء", callback_data=\'back_to_admin_menu\')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"الرجاء اختيار الصلاحية الجديدة للمستخدم بمعرف {user_id}:", reply_markup=reply_markup)
        return ADMIN_CHANGE_ROLE_NEW_ROLE
    except ValueError:
        await update.message.reply_text("معرف المستخدم غير صالح. الرجاء إرسال رقم صحيح.")
        return ADMIN_CHANGE_ROLE_ID

async def admin_receive_change_role_new_role(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    new_role = query.data.split(\'_\')[2]
    user_id = context.user_data.get(\'user_to_change_role\')

    db = SessionLocal()
    try:
        user_to_update = db.query(User).filter(User.user_id == user_id).first()
        if user_to_update:
            user_to_update.role = new_role
            db.commit()
            await query.edit_message_text(f"تم تغيير صلاحية المستخدم {user_to_update.username} (ID: {user_id}) إلى {new_role} بنجاح.")
        else:
            await query.edit_message_text(f"المستخدم بمعرف {user_id} غير موجود.")
    except Exception as e:
        await query.edit_message_text(f"حدث خطأ أثناء تغيير الصلاحية: {e}")
        db.rollback()
    finally:
        db.close()

    return await admin_menu(update, context)

async def template_password_handler(update: Update, context) -> int:
    password = update.message.text
    if password == TEMPLATE_PASSWORD_SECRET:
        await update.message.reply_text("كلمة المرور صحيحة. يرجى إرسال نص الخبر للقولبة:")
        return TEMPLATE_TEXT
    else:
        await update.message.reply_text("كلمة المرور غير صحيحة. الرجاء المحاولة مرة أخرى أو العودة للقائمة الرئيسية.")
        return TEMPLATE_PASSWORD

async def template_text_handler(update: Update, context) -> int:
    context.user_data[\'template_news_text\'] = update.message.text
    await update.message.reply_text("الرجاء إرسال الصورة المراد قولبتها:")
    return TEMPLATE_IMAGE

async def template_image_handler(update: Update, context) -> int:
    if not update.message.photo:
        await update.message.reply_text("الرجاء إرسال صورة. لا يمكن معالجة أنواع أخرى من الوسائط.")
        return TEMPLATE_IMAGE

    file_id = update.message.photo[-1].file_id
    news_text = context.user_data.get(\'template_news_text\')

    try:
        # Download the photo
        file = await context.bot.get_file(file_id)
        file_bytes = io.BytesIO()
        await file.download_to_memory(file_bytes)
        file_bytes.seek(0)

        # Process the image
        processed_image_bytes = process_template_image(file_bytes.getvalue(), news_text)

        # Send the processed image back
        await update.message.reply_photo(photo=processed_image_bytes, caption="الصورة بعد القولبة:")

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الصورة: {e}")
    finally:
        context.user_data.clear()

    return ConversationHandler.END

async def back_to_main_menu(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    await start(update, context)
    return MAIN_MENU

async def back_to_month_selection(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    return await select_month(update, context)

async def back_to_week_selection(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    return await select_week(update, context)

async def back_to_admin_menu(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    return await admin_menu(update, context)

async def back_to_admin_month_selection(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    return await admin_view_archive_month(update, context)

async def back_to_reports_menu(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    return await reports_menu(update, context)

async def back_to_report_month_selection(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    return await report_select_month(update, context)

# Main function to run the bot
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Initialize database and add default admin
    init_db(ADMIN_ID, "default_admin_username") # You might want to get admin username dynamically or from config

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(\'start\', start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler, pattern=\'^main_menu_\\w+$\'
)
            ],
            SELECT_MONTH: [
                CallbackQueryHandler(month_selection_handler, pattern=\'^month_\\w+$\'
),
                CallbackQueryHandler(back_to_main_menu, pattern=\'^back_to_main$\'
)
            ],
            SELECT_WEEK: [
                CallbackQueryHandler(week_selection_handler, pattern=\'^week_\\w+$\'
),
                CallbackQueryHandler(back_to_month_selection, pattern=\'^back_to_month_selection$\'
)
            ],
            SELECT_ACTIVITY: [
                CallbackQueryHandler(activity_selection_handler, pattern=\'^activity_\\w+$\'
),
                CallbackQueryHandler(back_to_week_selection, pattern=\'^back_to_week_selection$\'
)
            ],
            SEND_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_news_text)
            ],
            SEND_MEDIA: [
                CallbackQueryHandler(save_archive, pattern=\'^save_archive$\'
),
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.MIME_TYPE(\'application/pdf\'), receive_media)
            ],
            REPORTS_MENU: [
                CallbackQueryHandler(report_select_month, pattern=\'^report_weekly_select_month$|^report_monthly_select_month$\'
),
                CallbackQueryHandler(back_to_main_menu, pattern=\'^back_to_main$\'
)
            ],
            REPORT_SELECT_MONTH: [
                CallbackQueryHandler(report_month_selection_handler, pattern=\'^report_month_\\w+$\'
),
                CallbackQueryHandler(back_to_reports_menu, pattern=\'^back_to_reports_menu$\'
)
            ],
            REPORT_SELECT_WEEK: [
                CallbackQueryHandler(report_week_selection_handler, pattern=\'^report_week_\\w+$\'
),
                CallbackQueryHandler(back_to_report_month_selection, pattern=\'^back_to_report_month_selection$\'
)
            ],
            ADMIN_MENU: [
                CallbackQueryHandler(admin_view_archive_month, pattern=\'^admin_view_archive$\'
),
                CallbackQueryHandler(admin_manage_users, pattern=\'^admin_manage_users$\'
),
                CallbackQueryHandler(back_to_main_menu, pattern=\'^back_to_main$\'
)
            ],
            ADMIN_SELECT_MONTH: [
                CallbackQueryHandler(admin_month_selection_handler, pattern=\'^admin_month_\\w+$\'
),
                CallbackQueryHandler(back_to_admin_menu, pattern=\'^back_to_admin_menu$\'
)
            ],
            ADMIN_SELECT_WEEK: [
                CallbackQueryHandler(admin_week_selection_handler, pattern=\'^admin_week_\\w+$\'
),
                CallbackQueryHandler(back_to_admin_month_selection, pattern=\'^back_to_admin_month_selection$\'
)
            ],
            ADMIN_MANAGE_USERS: [
                CallbackQueryHandler(admin_add_user, pattern=\'^admin_add_user$\'
),
                CallbackQueryHandler(admin_remove_user, pattern=\'^admin_remove_user$\'
),
                CallbackQueryHandler(admin_change_role, pattern=\'^admin_change_role$\'
),
                CallbackQueryHandler(back_to_admin_menu, pattern=\'^back_to_admin_menu$\'
)
            ],
            ADMIN_ADD_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_add_user_id)
            ],
            ADMIN_ADD_USER_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_add_user_username)
            ],
            ADMIN_REMOVE_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_remove_user_id)
            ],
            ADMIN_CHANGE_ROLE_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_change_role_id)
            ],
            ADMIN_CHANGE_ROLE_NEW_ROLE: [
                CallbackQueryHandler(admin_receive_change_role_new_role, pattern=\'^change_role_\\w+$\'
),
                CallbackQueryHandler(back_to_admin_menu, pattern=\'^back_to_admin_menu$\'
) # Allow cancelling role change
            ],
            TEMPLATE_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, template_password_handler)
            ],
            TEMPLATE_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, template_text_handler)
            ],
            TEMPLATE_IMAGE: [
                MessageHandler(filters.PHOTO, template_image_handler)
            ]
        },
        fallbacks=[CommandHandler(\'start\', start)],
    )

    application.add_handler(conv_handler)

    print("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == \'__main__\':
    main()
