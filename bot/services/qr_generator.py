"""QR code generation service."""
import qrcode
from io import BytesIO
from typing import Optional
from pathlib import Path

from bot.config import settings
from bot.utils.logger import logger


class QRCodeGenerator:
    """Generate QR codes for users and tickets."""
    
    def __init__(self):
        self.base_url = settings.website_url
    
    def generate_user_profile_qr(
        self,
        user_id: int,
        username: Optional[str] = None
    ) -> BytesIO:
        """Generate QR code linking to user's public profile."""
        profile_url = f"{self.base_url}/profile/{user_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(profile_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        logger.info("qr_generated", user_id=user_id, type="profile")
        return buffer
    
    def generate_ticket_qr(
        self,
        ticket_id: int,
        ticket_code: str
    ) -> BytesIO:
        """Generate QR code for event ticket."""
        # Format: UPC-TICKET-{ticket_id}-{code}
        ticket_data = f"UPC-TICKET-{ticket_id}-{ticket_code}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(ticket_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#8B0000", back_color="white")  # Dark red
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        logger.info("qr_generated", ticket_id=ticket_id, type="ticket")
        return buffer
    
    def generate_referral_qr(self, referral_code: str) -> BytesIO:
        """Generate QR code for referral link."""
        referral_url = f"{self.base_url}/join?ref={referral_code}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(referral_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        logger.info("qr_generated", referral_code=referral_code, type="referral")
        return buffer
