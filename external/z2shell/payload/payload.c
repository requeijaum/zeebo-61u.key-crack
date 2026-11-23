/* Payload de prova — Zeebo/BREW 4.0.2 (arm-none-eabi-gcc)
 * Escreve "PAYLOAD_OK_ZWHEEL" em fs:/~/payload_ok.txt e encerra o applet.
 * ClassID = 0x01009FF0 (reutiliza helloworld.mif — MIF valido e ja presente).
 */
#include "AEEAppGen.h"
#include "AEEShell.h"
#include "AEEFile.h"
#include "AEEModGen.h"

#define AEECLSID_PAYLOAD 0x01009FF0

static boolean Payload_HandleEvent(AEEApplet *pme, AEEEvent eCode, uint16 w, uint32 dw)
{
   switch (eCode) {
   case EVT_APP_START: {
      IFileMgr *pfm = NULL;
      IFile *pf = NULL;
      const char *msg = "PAYLOAD_OK_ZWHEEL";

      if (ISHELL_CreateInstance(pme->m_pIShell, AEECLSID_FILEMGR,
                                (void **)&pfm) == SUCCESS && pfm != NULL) {
         pf = IFILEMGR_OpenFile(pfm, "payload_ok.txt", _OFM_CREATE);
         if (pf != NULL) {
            IFILE_Write(pf, msg, 17);
            IFILE_Release(pf);
         }
         IFILEMGR_Release(pfm);
      }
      ISHELL_CloseApplet(pme->m_pIShell, FALSE);
      return TRUE;
   }
   case EVT_APP_STOP:
      return TRUE;
   default:
      break;
   }
   return FALSE;
}

int AEEClsCreateInstance(AEECLSID ClsId, IShell *pIShell, IModule *pMod, void **ppObj)
{
   *ppObj = NULL;
   if (ClsId != AEECLSID_PAYLOAD)
      return ECLASSNOTSUPPORT;

   if (AEEApplet_New(sizeof(AEEApplet), ClsId, pIShell, pMod, (IApplet **)ppObj,
                     (AEEHANDLER)Payload_HandleEvent, NULL))
      return AEE_SUCCESS;

   return EFAILED;
}
