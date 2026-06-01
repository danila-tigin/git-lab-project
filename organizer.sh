#!/bin/bash

# ============================================
# ЛАБА №6: Организатор файлов
# Сортирует файлы по папкам в зависимости от расширения
# ============================================

# --- ШАГ 1: Создаём папки для разных типов файлов ---

# Папка для картинок
mkdir jpg_dir 2>/dev/null
mkdir png_dir 2>/dev/null

# Папка для текстовых файлов
mkdir txt_dir 2>/dev/null

# Папка для документов PDF
mkdir pdf_dir 2>/dev/null

# Папка для архивов
mkdir zip_dir 2>/dev/null

# Папка для скриптов
mkdir sh_dir 2>/dev/null

# Папка для всего остального
mkdir other_dir 2>/dev/null

# 2>/dev/null - это значит "если папка уже есть, не ругаться"

# --- ШАГ 2: Начинаем перебирать все файлы ---

# Берём каждый файл по очереди
for file in *; do
    
    # Проверяем: это вообще файл? (не папка, не ссылка)
    if [ -f "$file" ]; then
        
        # --- ШАГ 3: Узнаём расширение файла ---
        # Отрезаем всё до последней точки
        ext="${file##*.}"
        
        # --- ШАГ 4: Проверяем расширение и перемещаем ---
        
        # Если картинка jpg
        if [ "$ext" = "jpg" ] || [ "$ext" = "jpeg" ]; then
            mv "$file" jpg_dir/
            echo "Перемещён $file -> jpg_dir"
        
        # Если картинка png
        elif [ "$ext" = "png" ]; then
            mv "$file" png_dir/
            echo "Перемещён $file -> png_dir"
        
        # Если текстовый файл
        elif [ "$ext" = "txt" ]; then
            mv "$file" txt_dir/
            echo "Перемещён $file -> txt_dir"
        
        # Если PDF
        elif [ "$ext" = "pdf" ]; then
            mv "$file" pdf_dir/
            echo "Перемещён $file -> pdf_dir"
        
        # Если архив
        elif [ "$ext" = "zip" ] || [ "$ext" = "tar" ] || [ "$ext" = "gz" ]; then
            mv "$file" zip_dir/
            echo "Перемещён $file -> zip_dir"
        
        # Если скрипт bash/sh
        elif [ "$ext" = "sh" ] || [ "$ext" = "bash" ]; then
            mv "$file" sh_dir/
            echo "Перемещён $file -> sh_dir"
        
        # Всё остальное
        else
            mv "$file" other_dir/
            echo "Перемещён $file -> other_dir"
        fi
        
    fi
done

# --- ШАГ 5: Готово! ---
echo ""
echo "========== Сортировка закончена! =========="
echo "Проверь созданные папки:"
ls -d */