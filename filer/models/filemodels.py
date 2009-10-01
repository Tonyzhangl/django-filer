from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.auth import models as auth_models

from django.conf import settings
from filer.models.safe_file_storage import SafeFilenameFileSystemStorage
from filer.models.foldermodels import Folder
from filer import context_processors

fs = SafeFilenameFileSystemStorage()

IMAGE_FILER_UPLOAD_ROOT = getattr(settings,'IMAGE_FILER_UPLOAD_ROOT', 'catalogue')
DEFAULT_ICON_SIZES = (
        '32','48','64',
)
    

class File(models.Model):
    _icon = "file"
    folder = models.ForeignKey(Folder, related_name='all_files', null=True, blank=True)
    file_field = models.FileField(upload_to=IMAGE_FILER_UPLOAD_ROOT, storage=fs, null=True, blank=True,max_length=255)
    _file_type_plugin_name = models.CharField(_("file_type_plugin_name"), max_length=128, null=True, blank=True, editable=False)
    _file_size = models.IntegerField(null=True, blank=True)
    
    has_all_mandatory_data = models.BooleanField(default=False, editable=False)
    
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    
    owner = models.ForeignKey(auth_models.User, related_name='owned_%(class)ss', null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    # TODO: Factor out customer specific fields... maybe a m2m?
    #can_use_for_web = models.BooleanField(default=True)
    #can_use_for_print = models.BooleanField(default=True)
    #can_use_for_teaching = models.BooleanField(default=True)
    #can_use_for_research = models.BooleanField(default=True)
    #can_use_for_private_use = models.BooleanField(default=True)
    #usage_restriction_notes = models.TextField(null=True, blank=True)
    #notes = models.TextField(null=True, blank=True)
    #contact = models.ForeignKey(auth_models.User, related_name='contact_of_files', null=True, blank=True)
    
    @property
    def label(self):
        if self.name in ['',None]:
            text = self.original_filename or 'unnamed file'
        else:
            text = self.name
        text = u"%s [%s]" % (text, self.__class__.__name__)
        return text
    
    @property
    def icons(self):
        r = {}
        if getattr(self, '_icon', False):
            for size in DEFAULT_ICON_SIZES:
                r[size] = "%sicons/%s_%sx%s.png" % (context_processors.media(None)['FILER_MEDIA_URL'], self._icon, size, size)
        return r
    
    def has_edit_permission(self, request):
        return self.has_generic_permission(request, 'edit')
    def has_read_permission(self, request):
        return self.has_generic_permission(request, 'read')
    def has_add_children_permission(self, request):
        return self.has_generic_permission(request, 'add_children')
    def has_generic_permission(self, request, type):
        """
        Return true if the current user has permission on this
        image. Return the string 'ALL' if the user has all rights.
        """
        user = request.user
        if not user.is_authenticated() or not user.is_staff:
            return False
        elif user.is_superuser:
            return True
        elif user == self.owner:
            return True
        elif self.folder:
            return self.folder.has_generic_permission(request, type)
        else:
            return False
    
    def __unicode__(self):
        if self.name in ('', None):
            text = u"%s" % (self.original_filename,)
        else:
            text = u"%s" % (self.name,)
        return text
    def save(self, *args, **kwargs):
        # check if this is a subclass of "File" or not and set
        # _file_type_plugin_name
        if self.__class__ == File:
            # what should we do now?
            # maybe this has a subclass, but is being saved as a File instance
            # anyway. do we need to go check all possible subclasses?
            #self._file_type_plugin_name = 'GenericFile'
            pass
        elif issubclass(self.__class__, File):
            self._file_type_plugin_name = self.__class__.__name__
        return super(File, self).save(*args,**kwargs)
    
    def get_subtype(self):
        print "get subtype"
        if not self._file_type_plugin_name:
            r = self
        else:
            try:
                r = getattr(self, self._file_type_plugin_name.lower())
            except Exception, e:
                print e
                r = self
        print u"get_subtype: %s %s" % (r, self._file_type_plugin_name)
        return r
    class Meta:
        app_label = 'filer'