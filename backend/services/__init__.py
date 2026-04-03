"""
NeXifyAI Services Layer
- comms: Kanalübergreifender Kommunikationskern
- billing: Offer-to-Cash Status-Sync
- outbound: Outbound Lead Machine
"""

from services.comms import CommunicationService
from services.billing import BillingService

__all__ = ["CommunicationService", "BillingService"]
