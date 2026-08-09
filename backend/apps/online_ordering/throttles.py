from rest_framework.throttling import AnonRateThrottle
class PublicMenuThrottle(AnonRateThrottle):scope='public_menu'
class OnlineOrderThrottle(AnonRateThrottle):scope='online_order'
