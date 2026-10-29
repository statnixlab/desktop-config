#define _GNU_SOURCE
#include <dlfcn.h>
#include <link.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdatomic.h>

/* WPS 12.1.2.29183 / libkshell.so SHA-256:
 * 07c7b285c240f9cff2969667538b340767ca7eb20dcd237605d9d2d86dd7f744
 * In KMiniToolBarPopupWidget::eventFilter, QEvent::MouseMove (5) normally
 * branches to mouse-distance fading/dismissal. Redirect only that branch
 * to the existing QObject::eventFilter path. Button/key/custom events retain
 * their original paths. This is a private, in-process COW text-page change;
 * the packaged WPS library is never written. The launcher checks its hash.
 */
static atomic_int patched;
static _Thread_local int checking;
static bool enabled(void) {
    const char *flag=getenv("WPS_STICKY_SELECTION_TOOLBAR");
    if(!flag || strcmp(flag,"1"))return false;
    char path[4096];ssize_t n=readlink("/proc/self/exe",path,sizeof(path)-1);
    if(n<=0)return false;
    path[n]=0;const char *base=strrchr(path,'/');
    return base && (!strcmp(base+1,"wps") || !strcmp(base+1,"et"));
}
static void trace(const char *message) {
    const char *path=getenv("WPS_STICKY_TOOLBAR_LOG");
    if(!path)return;
    int fd=open(path,O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC,0600);
    if(fd>=0){dprintf(fd,"pid=%ld v3 %s\n",(long)getpid(),message);close(fd);}
}
static int inspect(struct dl_phdr_info *info,size_t size,void *unused) {
    (void)size;(void)unused;
    const char *base=strrchr(info->dlpi_name,'/');
    if(!base || strcmp(base+1,"libkshell.so"))return 0;
    uintptr_t address=info->dlpi_addr+0x161de80;
    const unsigned char before[]={0x83,0xf8,0x05,0x0f,0x84,0xe8,0x02,0x00,0x00};
    const unsigned char target[]={0x0f,0xb7,0x43,0x10};
    bool executable=false;
    for(int i=0;i<info->dlpi_phnum;i++){
        const ElfW(Phdr)*p=&info->dlpi_phdr[i];
        if(p->p_type==PT_LOAD && (p->p_flags&PF_X) &&
            0x161db2b>=p->p_vaddr && 0x161de89<=p->p_vaddr+p->p_memsz)executable=true;
    }
    if(!executable || memcmp((void*)address,before,sizeof(before)) ||
       memcmp((void*)(info->dlpi_addr+0x161db2b),target,sizeof(target))){
        trace("not applied: library instructions do not match supported version");
        atomic_store(&patched,-1);return 1;
    }
    long page_size=sysconf(_SC_PAGESIZE);
    if(page_size<=0)return 1;
    void *page=(void*)(address&~((uintptr_t)page_size-1));
    if(mprotect(page,(size_t)page_size,PROT_READ|PROT_WRITE|PROT_EXEC)){
        trace("not applied: cannot update private code page");return 1;
    }
    /* x86-64: replace the near-jump displacement in one 32-bit store. It
     * stays in one cache line. Runs on module load before GUI initialization. */
    __atomic_store_n((uint32_t*)(address+5),0xfffffca2u,__ATOMIC_SEQ_CST);
    __builtin___clear_cache((char*)address,(char*)(address+9));
    if(mprotect(page,(size_t)page_size,PROT_READ|PROT_EXEC))trace("warning: code-page protection restore failed");
    atomic_store(&patched,1);
    trace("applied: mini-toolbar mouse-move dismissal bypassed; click/key dismissal unchanged");
    return 1;
}
static void apply(void){
    if(checking || atomic_load(&patched) || !enabled())return;
    checking=1;dl_iterate_phdr(inspect,0);checking=0;
}
__attribute__((constructor)) static void startup(void){apply();}
void *dlopen(const char *path,int flags){
    typedef void*(*Open)(const char*,int);
    static Open original;
    if(!original)original=(Open)dlsym(RTLD_NEXT,"dlopen");
    if(!original)return 0;
    void *handle=original(path,flags);
    if(handle)apply();
    return handle;
}
