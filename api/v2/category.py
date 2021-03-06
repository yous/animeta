# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from api.v2 import BaseView
from api.serializers import serialize_category
from record.models import Category

class CategoryView(BaseView):
    def delete(self, request, id):
        category = get_object_or_404(Category, id=id)
        self.check_login()
        if request.user.id != category.user_id:
            self.raise_error('Permission denied.', status=403)
        category.record_set.update(category=None)
        category.delete()
        return {'ok': True}

    def post(self, request, id):
        category = get_object_or_404(Category, id=id)
        self.check_login()
        if request.user.id != category.user_id:
            self.raise_error('Permission denied.', status=403)
        category_name = request.POST.get('name')
        if not category_name:
            self.raise_error(u'분류 이름을 입력하세요.',
                status=400) # 400 Bad Request
        category.name = category_name
        category.save()
        return serialize_category(category)
