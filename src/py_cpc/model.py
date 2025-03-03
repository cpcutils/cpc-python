from dataclasses import dataclass, field
from typing import Optional

from .generated.client.models.mailpiece import Mailpiece as OpenapiMailpiece
from .generated.client.models.my_mail_notifications import MyMailNotifications
from .generated.client.types import Unset


@dataclass
class MailPiece:
  name: Optional[str]
  is_out_for_delivery: bool

  @staticmethod
  def from_openapi(mailpiece: OpenapiMailpiece):
    return MailPiece(
      name=mailpiece.mailer.name.en
      if not isinstance(mailpiece.mailer, Unset)
      else None,
      is_out_for_delivery=mailpiece.service_type != 25,
    )


@dataclass
class MailNotifications:
  mail_pieces: list[MailPiece] = field(default_factory=list)

  @staticmethod
  def from_openapi(notifications: MyMailNotifications):
    return MailNotifications(
      mail_pieces=[
        MailPiece.from_openapi(mp)
        for res in notifications.results
        for mp in res.mailpieces
      ]
    )
