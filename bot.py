from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import os
TOKEN = os.environ.get("TOKEN")
from nutricion import buscar_alimento
from database import init_db, guardar_comida, resumen_hoy, borrar_ultimo, historial_semana, obtener_objetivo, guardar_objetivo

COMIDAS = ["🌅 Desayuno", "☀️ Almuerzo", "🍎 Merienda", "🌙 Cena"]
COMIDAS_KEYS = ["desayuno", "almuerzo", "merienda", "cena"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy tu bot de dieta.\n\n"
        "Escríbeme un alimento y los gramos:\n"
        "➡️ *100g arroz*\n"
        "➡️ *200g pollo*\n\n"
        "📊 Usa /resumen para ver tu resumen del día.",
        parse_mode="Markdown"
    )

async def consultar_alimento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower().strip()
    partes = texto.split("g ", 1)
    if len(partes) != 2 or not partes[0].replace(".", "").isdigit():
        await update.message.reply_text(
            "⚠️ Formato correcto: *100g arroz*\nEjemplos:\n• 150g pollo\n• 200g avena",
            parse_mode="Markdown"
        )
        return

    gramos = float(partes[0])
    nombre = partes[1].strip()
    resultado = buscar_alimento(nombre, gramos)

    if not resultado:
        await update.message.reply_text(
            f"❌ No encontré '*{nombre}*'. Prueba en inglés.",
            parse_mode="Markdown"
        )
        return

    # Guardar datos temporalmente y preguntar la comida
    context.user_data["pendiente"] = {
        "resultado": resultado,
        "gramos": gramos
    }

    keyboard = [[InlineKeyboardButton(c, callback_data=f"comida_{COMIDAS_KEYS[i]}")] for i, c in enumerate(COMIDAS)]
    await update.message.reply_text(
        f"✅ *{resultado['nombre']}* ({gramos}g) — {resultado['kcal']} kcal\n\n¿En qué comida lo añado?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def seleccionar_comida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    comida = query.data.replace("comida_", "")
    user_id = query.from_user.id
    pendiente = context.user_data.get("pendiente")

    if not pendiente:
        await query.edit_message_text("⚠️ Ha habido un error, vuelve a introducir el alimento.")
        return

    r = pendiente["resultado"]
    gramos = pendiente["gramos"]

    guardar_comida(user_id, r['nombre'], gramos, r['kcal'], r['proteinas'], r['carbos'], r['grasas'], comida)
    context.user_data.pop("pendiente", None)

    emojis = {"desayuno": "🌅", "almuerzo": "☀️", "merienda": "🍎", "cena": "🌙"}
    await query.edit_message_text(
        f"🍽️ *{r['nombre']}* ({gramos}g) guardado en *{emojis[comida]} {comida.capitalize()}*\n\n"
        f"🔥 {r['kcal']} kcal | 💪 {r['proteinas']}g | 🍞 {r['carbos']}g | 🥑 {r['grasas']}g",
        parse_mode="Markdown"
    )

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    filas = resumen_hoy(user_id)

    if not filas:
        await update.message.reply_text("📭 Aún no has registrado nada hoy.")
        return

    emojis = {"desayuno": "🌅", "almuerzo": "☀️", "merienda": "🍎", "cena": "🌙"}
    bloques = {k: [] for k in COMIDAS_KEYS}
    total_kcal = total_prot = total_carbos = total_grasas = 0

    for alimento, gramos, kcal, prot, carbos, grasas, comida in filas:
        bloques[comida].append((alimento, gramos, kcal))
        total_kcal += kcal
        total_prot += prot
        total_carbos += carbos
        total_grasas += grasas

    texto = "📊 *Resumen de hoy:*\n"
    for key in COMIDAS_KEYS:
        if bloques[key]:
            subtotal = sum(k for _, _, k in bloques[key])
            texto += f"\n{emojis[key]} *{key.capitalize()}* — {round(subtotal, 1)} kcal\n"
            for alimento, gramos, kcal in bloques[key]:
                texto += f"  • {alimento} ({gramos}g) — {kcal} kcal\n"

    obj = obtener_objetivo(user_id)
    restantes = round(obj - total_kcal, 1)
    emoji = "✅" if restantes >= 0 else "⚠️"

    texto += f"\n🔥 *Total: {round(total_kcal, 1)} kcal*\n"
    texto += f"💪 Proteínas: {round(total_prot, 1)}g\n"
    texto += f"🍞 Carbohidratos: {round(total_carbos, 1)}g\n"
    texto += f"🥑 Grasas: {round(total_grasas, 1)}g\n"
    texto += f"\n{emoji} Objetivo: {obj} kcal — Te quedan *{restantes} kcal*"

    await update.message.reply_text(texto, parse_mode="Markdown")

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    eliminado = borrar_ultimo(user_id)
    if eliminado:
        await update.message.reply_text("🗑️ Último registro eliminado correctamente.")
    else:
        await update.message.reply_text("📭 No hay nada que borrar hoy.")

async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    filas = historial_semana(user_id)

    if not filas:
        await update.message.reply_text("📭 Aún no tienes historial registrado.")
        return

    texto = "📅 *Historial últimos 7 días:*\n\n"
    for fecha, kcal, prot, carbos, grasas in filas:
        emoji = "✅" if kcal <= 2500 else "⚠️"
        texto += f"{emoji} *{fecha}*\n"
        texto += f"   🔥 {round(kcal,1)} kcal | 💪 {round(prot,1)}g | 🍞 {round(carbos,1)}g | 🥑 {round(grasas,1)}g\n\n"

    await update.message.reply_text(texto, parse_mode="Markdown")

async def objetivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        obj = obtener_objetivo(user_id)
        await update.message.reply_text(f"🎯 Tu objetivo actual es *{obj} kcal*.\n\nPara cambiarlo: /objetivo 2200", parse_mode="Markdown")
        return

    try:
        nueva_kcal = float(context.args[0])
        guardar_objetivo(user_id, nueva_kcal)
        await update.message.reply_text(f"✅ Objetivo actualizado a *{nueva_kcal} kcal* diarias.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ Escribe un número válido. Ejemplo: /objetivo 2200")

init_db()

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("resumen", resumen))
app.add_handler(CommandHandler("borrar", borrar))
app.add_handler(CommandHandler("historial", historial))
app.add_handler(CommandHandler("objetivo", objetivo))
app.add_handler(CallbackQueryHandler(seleccionar_comida, pattern="^comida_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, consultar_alimento))

print("✅ Bot iniciado...")
app.run_polling()
