from rest_framework.routers import SimpleRouter

from referrals.views import ReferralProgramViewSet

router = SimpleRouter()
router.register("", ReferralProgramViewSet, basename="referrals")

urlpatterns = []

urlpatterns += router.urls
