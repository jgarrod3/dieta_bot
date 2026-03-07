from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN
from nutricion import buscar_alimento
from database import init_db, guardar_comida, resumen_hoy, borrar_ultimo, historial_semana, obtener_objetivo, guardar_objetivo

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola Juan! Soy tu bot de dieta.\n\n"
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

    # Guardar DESPUÉS de comprobar que resultado no es None
    guardar_comida(resultado['nombre'], gramos, resultado['kcal'],
                    resultado['proteinas'], resultado['carbos'], resultado['grasas'])

    await update.message.reply_text(
        f"🍽️ *{resultado['nombre']}* ({gramos}g)\n\n"
        f"🔥 Calorías: *{resultado['kcal']} kcal*\n"
        f"💪 Proteínas: {resultado['proteinas']}g\n"
        f"🍞 Carbohidratos: {resultado['carbos']}g\n"
        f"🥑 Grasas: {resultado['grasas']}g\n\n"
        f"✅ _Guardado en tu dieta del día_",
        parse_mode="Markdown"
    )

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filas = resumen_hoy()
    
    if not filas:
        await update.message.reply_text("📭 Aún no has registrado nada hoy.")
        return

    texto = "📊 *Resumen de hoy:*\n\n"
    total_kcal = total_prot = total_carbos = total_grasas = 0

    for fila in filas:
        alimento, gramos, kcal, prot, carbos, grasas = fila
        texto += f"• {alimento} ({gramos}g) — {kcal} kcal\n"
        total_kcal += kcal
        total_prot += prot
        total_carbos += carbos
        total_grasas += grasas

    restantes = round(2500 - total_kcal, 1)
    emoji = "✅" if restantes >= 0 else "⚠️"

    texto += f"\n🔥 *Total: {round(total_kcal, 1)} kcal*\n"
    texto += f"💪 Proteínas: {round(total_prot, 1)}g\n"
    texto += f"🍞 Carbohidratos: {round(total_carbos, 1)}g\n"
    texto += f"🥑 Grasas: {round(total_grasas, 1)}g\n"
    obj = obtener_objetivo()
    restantes = round(obj - total_kcal, 1)
    texto += f"\n{emoji} Objetivo: {obj} kcal — Te quedan *{restantes} kcal*"


    await update.message.reply_text(texto, parse_mode="Markdown")

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    eliminado = borrar_ultimo()
    if eliminado:
        await update.message.reply_text("🗑️ Último registro eliminado correctamente.")
    else:
        await update.message.reply_text("📭 No hay nada que borrar hoy.")


async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filas = historial_semana()

    if not filas:
        await update.message.reply_text("📭 Aún no tienes historial registrado.")
        return

    texto = "📅 *Historial últimos 7 días:*\n\n"
    for fila in filas:
        fecha, kcal, prot, carbos, grasas = fila
        emoji = "✅" if kcal <= 2500 else "⚠️"
        texto += f"{emoji} *{fecha}*\n"
        texto += f"   🔥 {round(kcal,1)} kcal | 💪 {round(prot,1)}g | 🍞 {round(carbos,1)}g | 🥑 {round(grasas,1)}g\n\n"

    await update.message.reply_text(texto, parse_mode="Markdown")


async def objetivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        obj = obtener_objetivo()
        await update.message.reply_text(f"🎯 Tu objetivo actual es *{obj} kcal*.\n\nPara cambiarlo: /objetivo 2200", parse_mode="Markdown")
        return
    
    try:
        nueva_kcal = float(context.args[0])
        guardar_objetivo(nueva_kcal)
        await update.message.reply_text(f"✅ Objetivo actualizado a *{nueva_kcal} kcal* diarias.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ Escribe un número válido. Ejemplo: /objetivo 2200")


init_db()

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("resumen", resumen))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, consultar_alimento))
app.add_handler(CommandHandler("borrar", borrar))
app.add_handler(CommandHandler("historial", historial))
app.add_handler(CommandHandler("objetivo", objetivo))

print("✅ Bot iniciado...")
app.run_polling()



