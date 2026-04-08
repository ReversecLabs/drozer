import OpenSSL

class CA(object):
    """
    CA represents a Certification Authority, capable of signing X509 certificates
    for use with SSL.
    """
    
    KEY_LENGTH = 2048
    
    def __init__(self):
        self.ca_key = None
        self.ca_cert = None
    
    @classmethod
    def certificate_to_pem(cls, certificate):
        """
        Convert an X509 certificate object into a PEM-encoded format.
        """
        
        return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate)
    
    @classmethod
    def pkey_to_pem(cls, pkey):
        """
        Convert an PKey certificate object into a PEM-encoded format.
        """
        
        return OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, pkey)
    
    def create_ca(self):
        """
        Create the key material for a CA, and use it to initialise this object.
        """
        
        self.ca_key = self.__generate_rsa_key()
        self.ca_cert = self.__generate_ca_certificate(self.ca_key)
        
        return True
    
    def create_certificate(self, cn="drozer"):
        """
        Create and sign a certificate, using the CA.
        """
        
        if self.has_ca():
            key = self.__generate_rsa_key()
            cert = self.__generate_certificate(key, cn)
            cert.set_issuer(self.ca_cert.get_subject())
            
            self.__sign_certificate(cert)
            
            return (key, cert)
        else:
            raise NoKeyMaterialError()
    
    def has_ca(self):
        """
        Returns True if this CA is initialised.
        """
        
        return self.ca_key != None and self.ca_cert != None
    
    def load(self, key, cert):
        """
        Load the key material for a CA, and use it to initialise this object.
        """
        
        self.ca_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        self.ca_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        
        if not self.verify_ca():
            self.ca_key = self.ca_cert = None
            
            return False
        else:
            return True
    
    def verify(self, key, certificate):
        """
        Check whether the a key/certificate pair match.
        """
        
        ctx = OpenSSL.SSL.Context(OpenSSL.SSL.TLS_METHOD)
        ctx.use_privatekey(key)
        ctx.use_certificate(certificate)
        
        try:
            ctx.check_privatekey()
        except OpenSSL.SSL.Error:
            return False
        except:
            pass
        
        return True
    
    def verify_ca(self):
        """
        Verify that the CA key material is valid.
        """
        
        return self.verify(self.ca_key, self.ca_cert)
        
    def __generate_ca_certificate(self, key):
        """
        Generate a new CA certificate - issued to 'drozer CA' and self-signed.
        """
        
        cert = self.__generate_certificate(key, "drozer CA")
        cert.set_issuer(cert.get_subject())
        self.__sign_certificate(cert)
        
        return cert
        
    def __generate_certificate(self, key, cn):
        """
        Generate an X509 certificate, valid for 1 year.
        """
        
        cert = OpenSSL.crypto.X509()
        cert.set_version(2)
        cert.set_serial_number(1)
        cert.get_subject().CN = cn
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365*24*3600)
        cert.set_pubkey(key)
        
        return cert
        
    def __generate_rsa_key(self):
        """
        Generate a new RSA key, that is KEY_LENGTH bits long.
        """
        
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, self.KEY_LENGTH)
        
        return key
    
    def __sign_certificate(self, cert):
        """
        Sign an X509 certificate with the CA.
        """
        
        cert.sign(self.ca_key, "sha1")
        
        
class NoKeyMaterialError(Exception):
    """
    Raised by CA if it is asked to perform signing operations with no valid CA key
    material.
    """
    
    pass
