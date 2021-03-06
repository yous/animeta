# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from api.v2 import BaseView
from api.serializers import serialize_record
from record.models import History

class PostView(BaseView):
    def delete(self, request, id):
        history = get_object_or_404(History, id=id)
        self.check_login()
        if request.user.id != history.user_id:
            self.raise_error('Permission denied.', status=403)
        if history.record.history_set.count() == 1:
            self.raise_error(u'등록된 작품마다 최소 1개의 기록이 필요합니다.',
                status=422) # 422 Unprocessable Entity
        history.delete()
        return {
            'record': serialize_record(history.record)
        }
