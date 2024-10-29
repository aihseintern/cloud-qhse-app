import logging
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session, Response, jsonify
from app.models import Document
from app import db
# from app.forms import DocumentForm

logging.basicConfig(level=logging.DEBUG)

document_bp = Blueprint('document', __name__, url_prefix='/document')

# DOCUMENT
