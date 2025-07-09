import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, flash, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Recipe, Product, Exercise
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

upload_folder = os.getenv('UPLOAD_FOLDER', 'static/images')
gif_upload_folder = os.getenv('GIF_UPLOAD_FOLDER', 'static/gifs')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, upload_folder)
app.config['GIF_UPLOAD_FOLDER'] = os.path.join(BASE_DIR, gif_upload_folder)

app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
# app.config['GIF_UPLOAD_FOLDER'] = os.getenv('GIF_UPLOAD_FOLDER')
# app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_static_file(relative_path):
    file_path = os.path.join(app.static_folder, relative_path)
    if os.path.exists(file_path):
        os.remove(file_path)

admins = {
    os.getenv("ADMIN_USERNAME"): os.getenv("ADMIN_PASSWORD_HASH")
}

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

@app.route('/admin/auth', methods=['GET', 'POST'])
def admin_auth():
    if session.get('is_admin'):
        return redirect(url_for('admin_recipes'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['is_admin'] = True
            flash('Вход выполнен')
            return redirect(url_for('admin_recipes'))
        else:
            flash('Неверный логин или пароль')

    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы')
    return redirect('/')

@app.route('/admin/recipes/', methods=['GET', 'POST'])
def admin_recipes():
    if not session.get('is_admin'):
        abort(404)
    print('Зашли в /admin')

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        ingredients = request.form.get('ingredients', '')
        file = request.files.get('file')

        if not title or not file or file.filename == '':
            flash('Название и изображение обязательны')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            recipes_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'recipes')
            os.makedirs(recipes_folder, exist_ok=True)

            filepath = os.path.join(recipes_folder, filename)
            file.save(filepath)

            new_recipe = Recipe(
                title=title,
                image_url='images/recipes/' + filename,
                description=description,
                ingredients=ingredients
            )
            db.session.add(new_recipe)
            db.session.commit()

            flash('Рецепт успешно добавлен')
            return redirect(url_for('admin_recipes'))
        else:
            flash('Неподдерживаемый формат файла')
            return redirect(request.url)

    recipes = Recipe.query.all()
    return render_template('admin_recipes.html', recipes=recipes)

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if not session.get('is_admin'):
        abort(404)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        calories = request.form.get('calories', type=float)
        protein = request.form.get('protein', type=float) or 0.0
        fat = request.form.get('fat', type=float) or 0.0
        carbs = request.form.get('carbs', type=float) or 0.0
        file = request.files.get('file')

        if not name or not file or file.filename == '':
            flash('Название и изображение обязательны')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'products', filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)

            new_product = Product(
                name=name,
                description=description,
                image_url='images/products/' + filename,
                calories=calories,
                protein=protein,
                fat=fat,
                carbs=carbs
            )
            db.session.add(new_product)
            db.session.commit()
            flash('Продукт успешно добавлен')
            return redirect(url_for('admin_products'))
        else:
            flash('Неподдерживаемый формат файла')
            return redirect(request.url)

    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/exercises/', methods=['GET', 'POST'])
def admin_exercises():
    if not session.get('is_admin'):
        abort(404)
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        category = request.form.get('category')
        file = request.files.get('gif_file')

        print("title:", name)
        print("category:", category)
        print("file:", file)
        print("file.filename:", getattr(file, 'filename', None))

        if not name or not category or not file or file.filename == '':
            flash('Название, категория и гифка обязательны')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = app.config['GIF_UPLOAD_FOLDER']
            os.makedirs(upload_path, exist_ok=True)
            filepath = os.path.join(upload_path, filename)
            file.save(filepath)

            new_exercise = Exercise(
                name=name,
                description=description,
                category=category,
                gif_url='gifs/' + filename
            )
            db.session.add(new_exercise)
            db.session.commit()

            flash('Упражнение успешно добавлено')
            return redirect(url_for('admin_exercises'))
        else:
            flash('Неподдерживаемый формат файла')
            return redirect(request.url)

    exercises = Exercise.query.all()
    categories = ['Руки', 'Грудь', 'Ноги', 'Плечи', 'Пресс', 'Ягодицы']
    return render_template('admin_exercises.html', exercises=exercises, categories=categories)

from flask import request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os

@app.route('/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.name = request.form['name']
    product.description = request.form['description']
    product.calories = request.form.get('calories', type=float)
    product.protein = request.form.get('protein', type=float)
    product.fat = request.form.get('fat', type=float)
    product.carbs = request.form.get('carbs', type=float)

    file = request.files.get('file')
    if file and file.filename:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)

            delete_static_file(product.image_url)

            product_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'products')
            os.makedirs(product_folder, exist_ok=True)

            filepath = os.path.join(product_folder, filename)
            file.save(filepath)

            product.image_url = f'images/products/{filename}'
        else:
            return jsonify({'error': 'Недопустимый формат файла'}), 400

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'image_url': product.image_url,
            'calories': product.calories,
            'protein': product.protein,
            'fat': product.fat,
            'carbs': product.carbs
        })

    return redirect(url_for('admin_products'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('is_admin'):
        abort(404)

    product = Product.query.get_or_404(product_id)
    delete_static_file(product.image_url)

    db.session.delete(product)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Продукт удалён')
    return redirect(url_for('admin_products'))


@app.route('/edit_recipe/<int:recipe_id>', methods=['POST'])
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    recipe.title = request.form['title']
    recipe.description = request.form['description']
    recipe.ingredients = request.form['ingredients']

    file = request.files.get('file')
    if file and file.filename:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)

            delete_static_file(recipe.image_url)

            recipe_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'recipes')
            os.makedirs(recipe_folder, exist_ok=True)

            filepath = os.path.join(recipe_folder, filename)
            file.save(filepath)

            recipe.image_url = f'images/recipes/{filename}'
        else:
            return jsonify({'error': 'Недопустимый формат файла'}), 400

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'id': recipe.id,
            'title': recipe.title,
            'description': recipe.description,
            'ingredients': recipe.ingredients,
            'image_url': recipe.image_url
        })

    return redirect(url_for('admin_recipes'))

@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    if not session.get('is_admin'):
        abort(404)

    recipe = Recipe.query.get_or_404(recipe_id)
    delete_static_file(recipe.image_url)

    db.session.delete(recipe)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Рецепт удалён')
    return redirect(url_for('admin_recipes'))

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/recipes')
def recipes_page():
    recipes = Recipe.query.all()
    return render_template('recipes.html', recipes=recipes)

@app.route("/sport")
def sport():
    return render_template("sport.html")

@app.route("/sport/arms")
def arms_exercises():
    exercises = Exercise.query.filter_by(category="Руки").all()
    return render_template("exercises.html", category_title="Упражнения на руки 💪", exercises=exercises)

@app.route("/sport/chest")
def chest_exercises():
    exercises = Exercise.query.filter_by(category="Грудь").all()
    return render_template("exercises.html", category_title="Упражнения на грудь 🏋️", exercises=exercises)

@app.route("/sport/legs")
def legs_exercises():
    exercises = Exercise.query.filter_by(category="Ноги").all()
    return render_template("exercises.html", category_title="Упражнения на ноги 🦵", exercises=exercises)

@app.route("/sport/shoulders")
def shoulders_exercises():
    exercises = Exercise.query.filter_by(category="Плечи").all()
    return render_template("exercises.html", category_title="Упражнения на плечи 🤷", exercises=exercises)

@app.route("/sport/abs")
def abs_exercises():
    exercises = Exercise.query.filter_by(category="Пресс").all()
    return render_template("exercises.html", category_title="Упражнения на пресс 🧘", exercises=exercises)

@app.route("/sport/glutes")
def glutes_exercises():
    exercises = Exercise.query.filter_by(category="Ягодицы").all()
    return render_template("exercises.html", category_title="Упражнения на ягодицы 🍑", exercises=exercises)

@app.route('/edit_exercise/<int:exercise_id>', methods=['POST'])
def edit_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    exercise.name = request.form['name']
    exercise.description = request.form['description']
    exercise.category = request.form['category']

    if 'gif_file' in request.files and request.files['gif_file'].filename:
        file = request.files['gif_file']
        filename = secure_filename(file.filename)
        folder = os.path.join(app.static_folder, 'gifs')
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        exercise.gif_url = f'gifs/{filename}'

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'category': exercise.category,
            'gif_url': exercise.gif_url
        })

    return redirect(url_for('admin_exercises'))

@app.route('/delete_exercise/<int:exercise_id>', methods=['POST'])
def delete_exercise(exercise_id):
    if not session.get('is_admin'):
        abort(404)

    exercise = Exercise.query.get_or_404(exercise_id)
    delete_static_file(exercise.gif_url)

    db.session.delete(exercise)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Упражнение удалено')
    return redirect(url_for('admin_exercises'))

@app.route('/products')
def products_page():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

from sqlalchemy import func

@app.route('/api/search_recipes')
def search_recipes():
    query = request.args.get('q', '').strip().lower()
    page = int(request.args.get('page', 1))
    per_page = 40

    all_recipes = Recipe.query.order_by(Recipe.id).all()

    if query:
        filtered = [r for r in all_recipes if query in r.title.lower()]
    else:
        filtered = all_recipes

    start = (page - 1) * per_page
    end = start + per_page
    paginated = filtered[start:end]

    result = [{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'ingredients': r.ingredients,
        'image_url': url_for('static', filename=r.image_url)
    } for r in paginated]

    return jsonify({
        'recipes': result,
        'has_next': end < len(filtered)
    })

@app.route('/api/recipes')
def api_recipes():
    page = int(request.args.get('page', 1))
    per_page = 40

    query = Recipe.query.order_by(Recipe.id)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    result = [{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'ingredients': r.ingredients,
        'image_url': url_for('static', filename=r.image_url)
    } for r in paginated.items]

    return jsonify({
        'recipes': result,
        'has_next': paginated.has_next,
        'page': page,
        'per_page': per_page,
        'total': paginated.total
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)