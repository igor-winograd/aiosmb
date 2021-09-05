from aiosmb.authentication.ntlm.structures.fields import Fields
from aiosmb.authentication.ntlm.structures.negotiate_flags import NegotiateFlags
from aiosmb.authentication.ntlm.structures.version import Version
from aiosmb.authentication.ntlm.structures.avpair import AVPairs, AVPAIRType

NTLMServerTemplates = {
		"Windows2003_nosig" : {
			'flags'      :  NegotiateFlags.NEGOTIATE_56|NegotiateFlags.NEGOTIATE_128|
							NegotiateFlags.NEGOTIATE_VERSION|NegotiateFlags.NEGOTIATE_TARGET_INFO|
							NegotiateFlags.NEGOTIATE_EXTENDED_SESSIONSECURITY|
							NegotiateFlags.TARGET_TYPE_DOMAIN|NegotiateFlags.NEGOTIATE_NTLM|
							NegotiateFlags.REQUEST_TARGET|NegotiateFlags.NEGOTIATE_UNICODE ,
			'version'    : Version.from_bytes(b"\x05\x02\xce\x0e\x00\x00\x00\x0f"),
			'targetinfo' : AVPairs({ AVPAIRType.MsvAvNbDomainName    : 'SMB',
								AVPAIRType.MsvAvNbComputerName       : 'SMB-TOOLKIT',
								AVPAIRType.MsvAvDnsDomainName        : 'smb.local',
								AVPAIRType.MsvAvDnsComputerName      : 'server2003.smb.local',
								AVPAIRType.MsvAvDnsTreeName          : 'smb.local',
						   }),

			'targetname' : 'SMB',
		},
		"Windows2003" : {
			'flags'      :  NegotiateFlags.NEGOTIATE_56|NegotiateFlags.NEGOTIATE_128|
							NegotiateFlags.NEGOTIATE_KEY_EXCH|NegotiateFlags.NEGOTIATE_ALWAYS_SIGN|NegotiateFlags.NEGOTIATE_SIGN|
							NegotiateFlags.NEGOTIATE_VERSION|NegotiateFlags.NEGOTIATE_TARGET_INFO|
							NegotiateFlags.NEGOTIATE_EXTENDED_SESSIONSECURITY|
							NegotiateFlags.TARGET_TYPE_DOMAIN|NegotiateFlags.NEGOTIATE_NTLM|
							NegotiateFlags.REQUEST_TARGET|NegotiateFlags.NEGOTIATE_UNICODE,
			'version'    : Version.from_bytes(b"\x05\x02\xce\x0e\x00\x00\x00\x0f"),
			'targetinfo' : AVPairs({ AVPAIRType.MsvAvNbDomainName    : 'SMB',
								AVPAIRType.MsvAvNbComputerName       : 'SMB-TOOLKIT',
								AVPAIRType.MsvAvDnsDomainName        : 'smb.local',
								AVPAIRType.MsvAvDnsComputerName      : 'server2003.smb.local',
								AVPAIRType.MsvAvDnsTreeName          : 'smb.local',
						   }),

			'targetname' : 'SMB',
		},
}