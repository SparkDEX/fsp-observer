from typing import TYPE_CHECKING, Self

from eth_account._utils.signing import to_standard_v
from eth_keys.datatypes import Signature as EthSignature
from eth_typing import ChecksumAddress
from py_flare_common.fsp.messaging.types import Signature as ParsedSignature

if TYPE_CHECKING:
    from ..types import ProtocolMessageRelayed


class Signature(EthSignature):
    @classmethod
    def from_parsed_signature(cls, s: ParsedSignature) -> Self:
        return cls(
            vrs=(
                to_standard_v(int(s.v, 16)),
                int(s.r, 16),
                int(s.s, 16),
            )
        )

    def signs_finalization(
        self,
        finalization: ProtocolMessageRelayed,
        chain_id: int,
        signer: ChecksumAddress,
    ) -> bool:
        # accepts either relay digest variant, see to_signed_hashes
        return any(
            self.recover_public_key_from_msg_hash(h).to_checksum_address() == signer
            for h in finalization.to_signed_hashes(chain_id)
        )
