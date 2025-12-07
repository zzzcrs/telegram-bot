import io
from datetime import datetime

import pandas as pd
from telegram import InputFile

from modules.homework import get_hw as db_get_hw
from modules.marks import get_marks as db_get_marks
from modules.tests import get_tests as db_get_tests


async def export_excel(update, context):
    """Экспорт данных в Excel"""
    uid = update.effective_user.id

    try:
        output = io.BytesIO()

        # Получаем данные
        marks = db_get_marks(uid)
        hw = db_get_hw(user_id=uid)
        tests = db_get_tests()

        # Если нет данных
        if not marks and not hw and not tests:
            await update.message.reply_text("❌ Нет данных для экспорта.")
            return

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Оценки
            if marks:
                marks_list = []
                for subject, marks_str in marks:
                    marks_list.append({"Предмет": subject, "Оценки": marks_str})

                df_marks = pd.DataFrame(marks_list)
                df_marks.to_excel(writer, sheet_name='Оценки', index=False)

            # 2. Домашняя работа
            if hw:
                hw_list = []
                for subject, text, due_date, date_added in hw:
                    hw_list.append({
                        "Предмет": subject,
                        "Задание": text,
                        "Срок": due_date or "без срока",
                        "Добавлено": date_added
                    })

                df_hw = pd.DataFrame(hw_list)
                df_hw.to_excel(writer, sheet_name='Домашка', index=False)

            # 3. Контрольные
            if tests:
                tests_list = []
                for subject, test_date, description in tests:
                    tests_list.append({
                        "Предмет": subject,
                        "Дата": test_date,
                        "Описание": description
                    })

                df_tests = pd.DataFrame(tests_list)
                df_tests.to_excel(writer, sheet_name='Контрольные', index=False)

        output.seek(0)

        filename = f"school_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        await update.message.reply_document(
            document=InputFile(output, filename=filename),
            caption="📊 Экспорт в Excel завершен!",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при экспорте: {str(e)[:100]}")
