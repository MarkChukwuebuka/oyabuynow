from django.db.models import Q

from crm.models import Color
from products.models import Category, Brand, Subcategory, Tag
from services.util import CustomRequestUtil



class CategoryService(CustomRequestUtil):


    def create_single(self, payload):

        name = payload.get("name")

        category, is_created = Category.objects.get_or_create(
            name__iexact=name,
            defaults=dict(
                name=name
            )
        )

        if not is_created:
            return None, self.make_error("There was an error creating the Category")


        return category, None

    def fetch_list(self, filter_params=None):
        q = Q()

        return self.get_base_query().filter(q)

    def get_base_query(self):
        qs = Category.available_objects.all()
        return qs

    def fetch_single_by_id(self, category_id):
        category = self.get_base_query().filter(id=category_id).first()
        if not category:
            return None, self.make_error("Category does not exist")

        return category, None


class SubcategoryService(CustomRequestUtil):

    def create_single(self, payload):

        name = payload.get("name")

        subcategory, is_created = Subcategory.objects.get_or_create(
            name__iexact=name,
            defaults=dict(
                name=name
            )
        )

        if not is_created:
            return None, self.make_error("There was an error creating the Subcategory")

        return subcategory, None


    def fetch_list(self, category_id):
        q = Q(category_id=category_id)

        return self.get_base_query().filter(q)

    def fetch_by_ids(self, subcategory_ids):
        return Subcategory.available_objects.filter(id__in=subcategory_ids)

    def get_base_query(self):
        qs = Subcategory.available_objects.select_related("category").all()
        return qs

    def fetch_single(self, subcategory_id):
        subcategory = self.get_base_query().filter(id=subcategory_id).first()
        if not subcategory:
            return None, self.make_error("Subcategory does not exist")

        return subcategory, None


class TagService(CustomRequestUtil):

    def create_single(self, payload):

        name = payload.get("name")

        tag, is_created = Tag.objects.get_or_create(
            name__iexact=name,
            defaults=dict(
                name=name
            )
        )

        if not is_created:
            return None, self.make_error("There was an error creating the Tag")

        return tag, None


    def fetch_list(self):
        q = Q()

        return self.get_base_query().filter(q)

    def fetch_by_ids(self, tag_ids):
        return Tag.available_objects.filter(id__in=tag_ids)

    def get_base_query(self):
        qs = Tag.available_objects.all()
        return qs

    def fetch_single(self, tag_id):
        tag = self.get_base_query().filter(id=tag_id).first()
        if not tag:
            return None, self.make_error("Tag does not exist")

        return tag, None



class ColorService(CustomRequestUtil):

    def create_single(self, payload):

        name = payload.get("name")

        color, is_created = Color.objects.get_or_create(
            name__iexact=name,
            defaults=dict(
                name=name
            )
        )

        if not is_created:
            return None, self.make_error("There was an error creating the Color")

        return color, None


    def fetch_list(self):
        q = Q()

        return self.get_base_query().filter(q)

    def fetch_by_ids(self, color_ids):
        return Color.objects.filter(id__in=color_ids)

    def get_base_query(self):
        qs = Color.objects.all()
        return qs

    def fetch_single_by_id(self, color_id):
        color = self.get_base_query().filter(id=color_id).first()
        if not color:
            return None, self.make_error("Color does not exist")

        return color, None



class BrandService(CustomRequestUtil):

    def create_single(self, payload):

        name = payload.get("name")

        brand, is_created = Brand.objects.get_or_create(
            name__iexact=name,
            defaults=dict(
                name=name
            )
        )

        if not is_created:
            return None, self.make_error("There was an error creating the Brand")


        return brand, None

    def fetch_list(self, filter_params=None):
        q = Q()

        return self.get_base_query().filter(q)

    def get_base_query(self):
        qs = Brand.available_objects.all()
        return qs


    def fetch_single_by_id(self, brand_id):
        brand = self.get_base_query().filter(id=brand_id).first()
        if not brand:
            return None, self.make_error("Brand does not exist")

        return brand, None