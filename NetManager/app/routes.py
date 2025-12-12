import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_from_directory, current_app, send_file
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app.models import db, User, Project, Device

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
projects_bp = Blueprint('projects', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== ROTAS DE AUTENTICAÇÃO ====================

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('projects.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar = request.form.get('confirmar_senha', '')
        
        if not all([username, email, senha, confirmar]):
            flash('Todos os campos são obrigatórios', 'danger')
        elif len(username) < 3:
            flash('Usuário deve ter no mínimo 3 caracteres', 'danger')
        elif len(senha) < 6:
            flash('Senha deve ter no mínimo 6 caracteres', 'danger')
        elif senha != confirmar:
            flash('Senhas não conferem', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Este usuário já existe', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Este email já está registrado', 'danger')
        else:
            user = User(username=username, email=email)
            user.set_password(senha)
            db.session.add(user)
            db.session.commit()
            flash('Conta criada com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/registro.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('projects.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        senha = request.form.get('senha', '')
        
        if not username or not senha:
            flash('Usuário e senha são obrigatórios', 'danger')
        else:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(senha):
                login_user(user, remember=True)
                flash('Login realizado com sucesso!', 'success')
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('projects.index'))
            else:
                flash('Usuário ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('auth.login'))


@projects_bp.route('/')
@projects_bp.route('/index')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)


@projects_bp.route('/project/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('Nome do projeto é obrigatório', 'danger')
            return render_template('project_create.html')
        
        filename = None
        if 'map' in request.files:
            file = request.files['map']
            if file and file.filename and allowed_file(file.filename):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = secure_filename(timestamp + file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
        project = Project(
            user_id=current_user.id,
            name=name,
            notes=notes,
            map_filename=filename
        )
        db.session.add(project)
        db.session.commit()
        flash('Projeto criado com sucesso!', 'success')
        return redirect(url_for('projects.edit_project', pid=project.id))
    
    return render_template('project_create.html')


@projects_bp.route('/project/<int:pid>')
@login_required
def view_project(pid):
    project = Project.query.get_or_404(pid)
    if project.user_id != current_user.id:
        flash('Você não tem permissão para acessar este projeto.', 'danger')
        return redirect(url_for('projects.index'))
    
    return render_template('project_view.html', project=project)


@projects_bp.route('/project/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(pid):
    project = Project.query.get_or_404(pid)
    if project.user_id != current_user.id:
        flash('Você não tem permissão para acessar este projeto.', 'danger')
        return redirect(url_for('projects.index'))
    
    if request.method == 'POST':
        project.name = request.form.get('name', project.name)
        project.notes = request.form.get('notes', project.notes)
        project.updated_at = datetime.utcnow()
        
        if 'map' in request.files:
            file = request.files['map']
            if file and file.filename and allowed_file(file.filename):
                if project.map_filename:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], project.map_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = secure_filename(timestamp + file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                project.map_filename = filename
        
        db.session.commit()
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('projects.edit_project', pid=project.id))
    
    return render_template('project_edit.html', project=project)


@projects_bp.route('/project/<int:pid>/delete', methods=['POST'])
@login_required
def delete_project(pid):
    project = Project.query.get_or_404(pid)
    if project.user_id != current_user.id:
        flash('Você não tem permissão para deletar este projeto.', 'danger')
        return redirect(url_for('projects.index'))
    
    # Remover arquivo de mapa
    if project.map_filename:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], project.map_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(project)
    db.session.commit()
    flash('Projeto deletado com sucesso!', 'success')
    return redirect(url_for('projects.index'))


@projects_bp.route('/api/project/<int:pid>')
@login_required
def api_get_project(pid):
    project = Project.query.get_or_404(pid)
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(project.to_dict())


@projects_bp.route('/api/project/<int:pid>/device', methods=['POST'])
@login_required
def api_add_device(pid):
    project = Project.query.get_or_404(pid)
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    device = Device(
        project_id=pid,
        device_type=data.get('device_type', 'router'),
        x=data.get('x', 0),
        y=data.get('y', 0),
        ip=data.get('ip'),
        name=data.get('name'),
        dns=data.get('dns'),
        gateway=data.get('gateway'),
        mac=data.get('mac'),
        notes=data.get('notes')
    )
    db.session.add(device)
    db.session.commit()
    return jsonify(device.to_dict()), 201


@projects_bp.route('/api/device/<int:did>', methods=['PUT', 'DELETE'])
@login_required
def api_modify_device(did):
    device = Device.query.get_or_404(did)
    project = device.project
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        device.device_type = data.get('device_type', device.device_type)
        device.x = data.get('x', device.x)
        device.y = data.get('y', device.y)
        device.ip = data.get('ip', device.ip)
        device.name = data.get('name', device.name)
        device.dns = data.get('dns', device.dns)
        device.gateway = data.get('gateway', device.gateway)
        device.mac = data.get('mac', device.mac)
        device.notes = data.get('notes', device.notes)
        db.session.commit()
        return jsonify(device.to_dict())
    
    elif request.method == 'DELETE':
        db.session.delete(device)
        db.session.commit()
        return jsonify({'message': 'Device deleted'}), 204


@projects_bp.route('/project/<int:pid>/relatorio')
@login_required
def gerar_relatorio(pid):
    project = Project.query.get_or_404(pid)
    if project.user_id != current_user.id:
        flash('Você não tem permissão para acessar este projeto.', 'danger')
        return redirect(url_for('projects.index'))
    
    now = datetime.now()
    return render_template('relatorio.html', project=project, now=now)



@projects_bp.route('/api/project/<int:pid>/relatorio/pdf')
@login_required
def api_gerar_pdf(pid):
    project = Project.query.get_or_404(pid)
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    buffer = io.BytesIO()
    p = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, height - 60, f'Relatório - {project.name}')
    p.setFont('Helvetica', 10)
    p.drawString(40, height - 80, f'Gerado por: {current_user.username}')
    p.drawString(300, height - 80, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')

    y = height - 110
    if project.notes:
        p.setFont('Helvetica-Bold', 12)
        p.drawString(40, y, 'Observações:')
        y -= 16
        p.setFont('Helvetica', 10)
        text = p.beginText(40, y)
        for line in str(project.notes).splitlines():
            text.textLine(line)
            y -= 12
        p.drawText(text)
        y -= 10
    if project.map_filename:
        try:
            img_path = os.path.join(current_app.config['UPLOAD_FOLDER'], project.map_filename)
            img = ImageReader(img_path)
            max_w = width - 80
            max_h = 250
            p.drawImage(img, 40, y - max_h, width=max_w, height=max_h, preserveAspectRatio=True, anchor='sw')
            y -= (max_h + 10)
        except Exception:
            pass
    p.setFont('Helvetica-Bold', 12)
    p.drawString(40, y, 'Dispositivos:')
    y -= 18
    p.setFont('Helvetica', 9)
    headers = ['Nome', 'Tipo', 'IP', 'MAC', 'Gateway', 'DNS']
    col_x = [40, 160, 260, 340, 420, 500]
    for i, h in enumerate(headers):
        p.drawString(col_x[i], y, h)
    y -= 14
    p.line(40, y, width - 40, y)
    y -= 6

    for device in project.devices:
        if y < 80:
            p.showPage()
            y = height - 60
            p.setFont('Helvetica', 9)
        p.drawString(col_x[0], y, (device.name or '-')[:18])
        p.drawString(col_x[1], y, (getattr(device, 'device_type', None) or getattr(device, 'type', '-'))[:12])
        p.drawString(col_x[2], y, (device.ip or '-')[:15])
        p.drawString(col_x[3], y, (device.mac or '-')[:15])
        p.drawString(col_x[4], y, (device.gateway or '-')[:12])
        p.drawString(col_x[5], y, (device.dns or '-')[:12])
        y -= 14

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f'relatorio_{project.id}.pdf', mimetype='application/pdf')


@projects_bp.route('/uploads/maps/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
