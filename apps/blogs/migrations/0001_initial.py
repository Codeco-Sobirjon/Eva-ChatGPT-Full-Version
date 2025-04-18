# Generated by Django 5.1.7 on 2025-04-07 17:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=500, null=True, verbose_name='Название')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('created_at', models.DateField(auto_now_add=True, null=True, verbose_name='Дата публикации')),
            ],
            options={
                'verbose_name': 'Блоги',
                'verbose_name_plural': 'Блоги',
            },
        ),
        migrations.CreateModel(
            name='BlogImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='blog/images/', verbose_name='')),
                ('blog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='blogs.blog', verbose_name='Блог')),
            ],
            options={
                'verbose_name': 'Изображения блога',
                'verbose_name_plural': 'Изображения блога',
            },
        ),
    ]
