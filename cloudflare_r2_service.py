"""
Servicio para subir archivos PDF a Cloudflare R2
Compatible con API S3 usando boto3
"""
import boto3
import threading
from botocore.exceptions import ClientError
from datetime import datetime


class CloudflareR2Service:
    def __init__(self):
        self._s3_client = None
        self._bucket_name = 'club-puntos'
        self._public_url = 'https://pub-b5aab2bd614a438ca24b96ebef0f97b3.r2.dev'
        self._initialize()
    
    def _initialize(self):
        """Inicializa el cliente boto3 con credenciales de Cloudflare R2"""
        try:
            self._s3_client = boto3.client(
                's3',
                endpoint_url='https://bd9123fa0a487d4429430199ce2073df.r2.cloudflarestorage.com',
                aws_access_key_id='66fc8d82db20ce9120d2d73828da0dc7',
                aws_secret_access_key='ef4215ecf89c933c3636578561cca0515d62c8ec273264ba03af7ad33804a84e',
                region_name='auto'
            )
        except Exception as e:
            print(f"❌ Error inicializando cliente R2: {e}")
    
    def upload_pdf(self, pdf_content: bytes, cedula: str, filename: str):
        """
        Sube un PDF a Cloudflare R2
        
        Args:
            pdf_content: Contenido del PDF en bytes
            cedula: Documento del usuario (para organizar en carpetas)
            filename: Nombre del archivo
            
        Returns:
            tuple: (success: bool, url: str, error: str)
        """
        try:
            # Estructura: consentimientos/{cedula}/{filename}
            object_key = f"consentimientos/{cedula}/{filename}"
            
            self._s3_client.put_object(
                Bucket=self._bucket_name,
                Key=object_key,
                Body=pdf_content,
                ContentType='application/pdf',
                ACL='public-read'
            )
            
            # URL pública del archivo
            public_url = f"{self._public_url}/{object_key}"
            return True, public_url, None
            
        except ClientError as e:
            error_msg = f"Error de cliente S3: {str(e)}"
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            return False, None, error_msg
    
    def upload_async(self, pdf_content: bytes, cedula: str, documento_id: str, callback=None):
        """
        Sube un PDF de forma asíncrona en un thread separado
        
        Args:
            pdf_content: Contenido del PDF en bytes
            cedula: Documento del usuario
            documento_id: ID del registro en BD
            callback: Función a ejecutar después de la subida
                     Firma: callback(success, url, error, documento_id)
        """
        def upload_background():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"CONSENT_{cedula}_{timestamp}.pdf"
            
            success, url, error = self.upload_pdf(pdf_content, cedula, filename)
            
            if callback:
                try:
                    callback(success, url, error, documento_id)
                except Exception as e:
                    pass  # Error manejado en el callback
        
        # Iniciar thread daemon (no bloquea el cierre de la app)
        thread = threading.Thread(target=upload_background, daemon=True)
        thread.start()


# Instancia global del servicio
r2_service = CloudflareR2Service()
