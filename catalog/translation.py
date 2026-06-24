from modeltranslation.translator import TranslationOptions, register

from .models import Category, Color, Product, ProductImage, ProductSpec


@register(Color)
class ColorTR(TranslationOptions):
    fields = ("name",)


@register(Category)
class CategoryTR(TranslationOptions):
    fields = ("name", "description")


@register(Product)
class ProductTR(TranslationOptions):
    fields = ("name", "short_description", "description")


@register(ProductSpec)
class ProductSpecTR(TranslationOptions):
    fields = ("name", "value")


@register(ProductImage)
class ProductImageTR(TranslationOptions):
    fields = ("alt",)
