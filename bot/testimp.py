import os
import logging
from PIL import Image, ImageDraw, ImageFont
import requests
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

print('Hi')