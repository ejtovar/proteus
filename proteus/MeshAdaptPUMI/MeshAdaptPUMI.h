#include "mesh.h"
#include <apf.h>
#include <apfMesh2.h>
#include <apfNumbering.h>
#include <queue>
#include "PyEmbeddedFunctions.h"

/**
   \file MeshAdaptPUMI.h
   \defgroup MeshAdaptPUMI MeshAdaptPUMI
   \brief A C-library of functions that uses SCOREC tools for error estimation and mesh adaptation
   @{
*/

/**
  @brief Class that handles the interface between SCOREC tools and Proteus
*/

class MeshAdaptPUMIDrvr{
 
  public:
  MeshAdaptPUMIDrvr(); 
  ~MeshAdaptPUMIDrvr();

  int loadModelAndMesh(const char* modelFile, const char* meshFile); //load the model and mesh
  int loadMeshForAnalytic(const char* meshFile,double* boxDim, double* sphereCenter, double radius); //mesh and construct analytic geometry
  void writeMesh(const char* meshFile);
  void cleanMesh();

  //Functions to construct proteus mesh data structures
  int reconstructFromProteus(Mesh& mesh, Mesh& globalMesh,int hasModel);
  int reconstructFromProteus2(Mesh& mesh, int* isModelVert, int* bFaces);
  int constructFromSerialPUMIMesh(Mesh& mesh);
  int constructFromParallelPUMIMesh(Mesh& mesh, Mesh& subdomain_mesh);
  int updateMaterialArrays(Mesh& mesh,int dim, int bdryID, int GeomTag);
  int updateMaterialArrays(Mesh& mesh);
  int updateMaterialArrays2(Mesh& mesh);
  void numberLocally();
  int localNumber(apf::MeshEntity* e);
  int dumpMesh(Mesh& mesh);

  //Functions used to transfer proteus model data structures
  int transferModelInfo(int*numGeomEntities,int*edges,int*faces,int*mVertex2Model,int*mEdgeVertex2Model,int*mBoundary2Model,int nMaxSegments);
  int numSegments;
  int* edgeList;
  int* faceList;
  int* meshVertex2Model, *meshEdge2Model, *meshBoundary2Model;
  int numModelEntities[4];

  //Functions used to transfer information between PUMI and proteus
  int transferFieldToPUMI(const char* name, double const* inArray, int nVar, int nN);
  int transferFieldToProteus(const char* name, double* outArray, int nVar, int nN);
  int transferElementFieldToProteus(const char* name, double* outArray, int nVar, int nN);
  int transferPropertiesToPUMI(double* rho_p, double* nu_p,double* g_p, double deltaT, double deltaT_next,double T_simulation,double interfaceBandSize);
  //int setAdaptProperties(std::vector<std::string> sizeInputs,double hmax);
  int setAdaptProperties(std::vector<std::string> sizeInputs,bool in_adapt, double in_hmax,double in_hmin,double in_hphi, int in_numAdaptSteps, double in_targetError, double in_gradingFactor, bool in_logging, int in_numIterations);
  //int transferBCtagsToProteus(int* tagArray, int idx, int* ebN, int* eN_global, double* fluxBC);
  //int transferBCsToProteus();

  //MeshAdapt functions
  int willAdapt();
  int willErrorAdapt();
  int willErrorAdapt_reference();
  int willInterfaceAdapt();
  int adaptPUMIMesh(const char* input);
  int setSphereSizeField();
  int calculateSizeField(double L_band);
  void predictiveInterfacePropagation();

  int calculateAnisoSizeField();
  int testIsotropicSizeField();
  int getERMSizeField(double err_total);
  int gradeMesh(double gradationFactor);

  //analytic geometry
  gmi_model* createSphereInBox(double* boxDim, double*sphereCenter,double radius);
  void updateSphereCoordinates(double*sphereCenter);

  //Quality Check Functions
  double getMinimumQuality();
  double getTotalMass();

  //Functions that help facilitate computations
  double getMPvalue(double field_val,double val_0, double val_1); //get the multiphase value of physical properties
  apf::Field* getViscosityField(apf::Field* voff); //derive a field of viscosity based on VOF field

  //needed for checkpointing/restart
  void set_nAdapt(int numberAdapt);

  //Public Variables
  double hmax, hmin, hPhi; //bounds on mesh size
  int numIter; //number of iterations for MeshAdapt
  int nAdapt; //counter for number of adapt steps
  int nTriggers; //counter for number of triggers
  int nEstimate; //counter for number of error estimator calls
  int nsd; //number of spatial dimensions
  int maxAspect; //maximum aspect ratio
  int adaptMesh; //is adaptivity turned on?
  int numAdaptSteps; //Number adaptivity
  double N_interface_band; //number of elements in half-band around interface
  double gradingFactor;
  bool hasIBM;
  bool hasInterface;
  bool hasVMS;
  bool hasERM;
  bool hasAniso;
  bool hasAnalyticSphere;
  bool useProteus; 
  bool useProteusAniso;

  

  //User Inputs
  std::string size_field_config; //What type of size field: interface, ERM, isotropic
  std::string adapt_type_config; //What type of adapt for ERM: isotropic or anisotropic
  std::string logging_config; // Logging on or off

  //Element Residual Method
  void get_local_error(double& total_error);
  void computeDiffusiveFlux(apf::Mesh*m,apf::Field* voff, apf::Field* visc,apf::Field* pref, apf::Field* velf);
  void getBoundaryFlux(apf::Mesh* m, apf::MeshEntity* ent, double * endflux);
  int getSimmetrixBC();
  void removeBCData();
  char* modelFileName; 
  
  //VMS
  void get_VMS_error(double& total_error_out);
  
  //tags used to identify types of BC
  apf::MeshTag* BCtag;
  apf::MeshTag* DBCtag[4];
  apf::MeshTag* fluxtag[4];

  int *exteriorGlobaltoLocalElementBoundariesArray;

  //Approximation/Integration order
  int approximation_order; //what order polynomial (hierarchic is 2nd order)
  int integration_order; //determines number of integration points
  int num_quadrature; 
  int num_quadrature_boundary;
  double total_error;
  double errRho_max;
  double rel_err_total;

  //Mesh Reconstruction
  int isReconstructed;
  int initialReconstructed;
  int* modelVertexMaterial; 
  int* modelBoundaryMaterial;
  int* modelRegionMaterial;
  int numModelOffsets[4];
  int numModelTotals[4];

  private: 
  apf::Mesh2* m;
  int comm_size, comm_rank;

  //double rho[2];
  //nu[2];
  double* rho;
  double* nu;

  double g[3];
  double delta_T;
  double delta_T_next;
  double T_current; //for error trigger
  double T_reference; //for error trigger

  apf::MeshTag* diffFlux;
  apf::GlobalNumbering* global[4];
  apf::Numbering* local[4];
  apf::Field* err_reg; //error field from ERM
  apf::Field* vmsErrH1; //error field for VMS
  apf::Field* errRho_reg; //error-density field from ERM
  apf::Field* errRel_reg; //relative error field from ERM
  apf::Field* error_reference;

  /* this field stores isotropic size */
  apf::Field* size_iso;
  /* these fields store anisotropic size and metric tensor */
  apf::Field* size_scale;
  apf::Field* size_frame;

  //queue for size fields
  std::queue<apf::Field*> sizeFieldList;
  void isotropicIntersect();

  int constructGlobalNumbering(Mesh& mesh);
  int constructGlobalStructures(Mesh& mesh);

  int constructElements(Mesh& mesh);
  int constructNodes(Mesh& mesh);
  int constructBoundaries(Mesh& mesh);
  int constructEdges(Mesh& mesh);
  int constructMaterialArrays(Mesh& mesh);

  void freeField(apf::Field*& f);
  void freeNumbering(apf::Numbering*& n);

  static void averageToEntity(apf::Field* ef, apf::Field* vf,
      apf::MeshEntity* ent);
  void volumeAverageToEntity(apf::Field* ef, apf::Field* vf,
      apf::MeshEntity* ent);
  static void minToEntity(apf::Field* ef, apf::Field* vf,
      apf::MeshEntity* ent);

  bool has_gBC; //boolean for having global boundary conditions
  double target_error; //computed from get_local_error()
  int target_element_count; //How many elements in the mesh are desired?
  double domainVolume; //Volume of the domain
  double THRESHOLD; //threshold of error before adapt
};


/** @} */
