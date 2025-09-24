from django.db.models import Q
from django.utils import timezone

from products.models import DealOfTheDay, TopShopper
from services.util import CustomRequestUtil




class DOTDService(CustomRequestUtil):

    def fetch_active_deals(self):
        q = Q(is_active=True)

        return self.get_base_query().filter(q)


    def get_base_query(self):
        return DealOfTheDay.objects.select_related("product")

    def toggle_active_state(self):

        now = timezone.now()
        for deal in DealOfTheDay.objects:
            deal.is_active = True if deal.start_time <= now <= deal.end_time else False
            deal.save()

        return None


class TopShopperService(CustomRequestUtil):

    def fetch_list(self):
        return self.get_base_query()[:3]


    def get_base_query(self):
        return TopShopper.objects.order_by('-id')
