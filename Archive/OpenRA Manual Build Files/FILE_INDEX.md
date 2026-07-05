# OpenRA Engine Source File Catalog

This catalog lists every C# source file in the OpenRA engine, grouped by project and directory. It is used to ensure the manual covers every subsystem.

## OpenRA.Game (226 files)

### 

- Actor.cs
- CPos.cs
- CryptoUtil.cs
- CVec.cs
- DefaultPlayer.cs
- DescAttribute.cs
- ExternalMods.cs
- Exts.cs
- FieldLoader.cs
- FieldSaver.cs
- FluentBundle.cs
- FluentExts.cs
- FluentProvider.cs
- Fonts.cs
- Game.cs
- GameInformation.cs
- GameSpeed.cs
- HotkeyDefinition.cs
- HotkeyManager.cs
- HttpExtension.cs
- InstalledMods.cs
- IUtilityCommand.cs
- LocalPlayerProfile.cs
- Manifest.cs
- MiniYaml.cs
- ModData.cs
- MPos.cs
- ObjectCreator.cs
- Platform.cs
- Player.cs
- PlayerDatabase.cs
- PlayerProfile.cs
- Renderer.cs
- SelectableExts.cs
- Settings.cs
- StreamExts.cs
- Sync.cs
- TextNotification.cs
- TextNotificationsManager.cs
- TraitDictionary.cs
- VoiceExts.cs
- WAngle.cs
- WDist.cs
- World.cs
- WorldUtils.cs
- WorldViewportSizes.cs
- WPos.cs
- WRot.cs
- WVec.cs

### Activities

- Activity.cs
- CallFunc.cs

### Effects

- DelayedAction.cs
- DelayedImpact.cs
- IEffect.cs

### FileFormats

- CRC32.cs
- Png.cs
- ReplayMetadata.cs

### FileSystem

- FileSystem.cs
- Folder.cs
- IPackage.cs
- ZipFile.cs

### GameRules

- ActorInfo.cs
- MusicInfo.cs
- Ruleset.cs
- SoundInfo.cs
- WeaponInfo.cs

### Graphics

- Animation.cs
- AnimationWithOffset.cs
- ChromeProvider.cs
- CursorManager.cs
- CursorSequence.cs
- HardwarePalette.cs
- MarkerTileRenderable.cs
- Model.cs
- ModelAnimation.cs
- ModelVertex.cs
- Palette.cs
- PaletteReference.cs
- PlatformInterfaces.cs
- PlayerColorRemap.cs
- Renderable.cs
- RenderPostProcessPassVertex.cs
- RgbaColorRenderer.cs
- RgbaSpriteRenderer.cs
- SequenceSet.cs
- ShaderBindings.cs
- Sheet.cs
- SheetBuilder.cs
- Sprite.cs
- SpriteCache.cs
- SpriteFont.cs
- SpriteLoader.cs
- SpriteRenderable.cs
- SpriteRenderer.cs
- TargetLineRenderable.cs
- TerrainSpriteLayer.cs
- UISpriteRenderable.cs
- Util.cs
- Vertex.cs
- Video.cs
- VideoLoader.cs
- Viewport.cs
- WorldRenderer.cs

### Input

- Hotkey.cs
- HotkeyReference.cs
- IInputHandler.cs
- InputHandler.cs
- Keycode.cs

### Map

- ActorInitializer.cs
- ActorReference.cs
- CellCoordsRegion.cs
- CellLayer.cs
- CellLayerBase.cs
- CellRegion.cs
- Map.cs
- MapCache.cs
- MapCoordsRegion.cs
- MapDirectoryTracker.cs
- MapGenerationArgs.cs
- MapGrid.cs
- MapPlayers.cs
- MapPreview.cs
- PlayerReference.cs
- ProjectedCellLayer.cs
- ProjectedCellRegion.cs
- TerrainInfo.cs
- TileReference.cs

### Network

- Connection.cs
- ConnectionTarget.cs
- FluentMessage.cs
- GameSave.cs
- GameServer.cs
- GeoIP.cs
- Handshake.cs
- Nat.cs
- Order.cs
- OrderIO.cs
- OrderManager.cs
- ReplayConnection.cs
- ReplayRecorder.cs
- Session.cs
- SyncReport.cs
- TickTime.cs
- UnitOrders.cs

### Orders

- IOrderGenerator.cs

### Primitives

- ActionQueue.cs
- ActorInfoDictionary.cs
- BitSet.cs
- Cache.cs
- CachedTransform.cs
- Color.cs
- ConcurrentCache.cs
- DisposableAction.cs
- float2.cs
- float3.cs
- int2.cs
- Int32Matrix4x4.cs
- IObservableCollection.cs
- LongBitSet.cs
- MergedStream.cs
- ObservableCollection.cs
- ObservableDictionary.cs
- ObservableList.cs
- PlayerDictionary.cs
- Polygon.cs
- PredictedCachedTransform.cs
- PriorityArray.cs
- PriorityQueue.cs
- ReadOnlyAdapterStream.cs
- Rectangle.cs
- RingBuffer.cs
- SegmentStream.cs
- Size.cs
- SpatiallyPartitioned.cs
- TypeDictionary.cs

### Scripting

- ScriptActorInterface.cs
- ScriptContext.cs
- ScriptMemberExts.cs
- ScriptMemberWrapper.cs
- ScriptObjectWrapper.cs
- ScriptPlayerInterface.cs
- ScriptTypes.cs

### Server

- Connection.cs
- Exts.cs
- MapStatusCache.cs
- OrderBuffer.cs
- PlayerMessageTracker.cs
- ProtocolVersion.cs
- Server.cs
- TraitInterfaces.cs
- VoteKickTracker.cs

### Sound

- Sound.cs
- SoundDevice.cs

### Support

- Arguments.cs
- AssemblyLoader.cs
- Benchmark.cs
- ExceptionHandler.cs
- HttpClientFactory.cs
- HttpQueryBuilder.cs
- LaunchArguments.cs
- Log.cs
- MersenneTwister.cs
- PerfHistory.cs
- PerfItem.cs
- PerfSample.cs
- PerfTickLogger.cs
- PerfTimer.cs
- Program.cs
- VariableExpression.cs

### Traits

- ActivityUtils.cs
- DebugPauseState.cs
- LintAttributes.cs
- Target.cs
- TraitsInterfaces.cs

### Traits\Player

- FrozenActorLayer.cs
- Shroud.cs

### Traits\World

- DebugVisualizations.cs
- Faction.cs
- ScreenMap.cs
- ScreenShaker.cs

### UtilityCommands

- ClearInvalidModRegistrationsCommand.cs
- RegisterModCommand.cs
- UnregisterModCommand.cs

### Widgets

- ChromeMetrics.cs
- Widget.cs
- WidgetLoader.cs

## OpenRA.Mods.Common (1082 files)

### 

- ActorExts.cs
- ActorIndex.cs
- ActorInitializer.cs
- AIUtils.cs
- AssetBrowser.cs
- DiscordService.cs
- ItchIntegration.cs
- ModContent.cs
- ModCredits.cs
- PlayerExtensions.cs
- ShroudExts.cs
- TargetExtensions.cs
- TraitsInterfaces.cs
- Util.cs
- WebServices.cs
- WorldExtensions.cs

### Activities

- Attack.cs
- CaptureActor.cs
- DeliverUnit.cs
- Demolish.cs
- DeployForGrantedCondition.cs
- DonateCash.cs
- DonateExperience.cs
- Enter.cs
- FindAndDeliverResources.cs
- GenericDockSequence.cs
- HarvestResource.cs
- Hunt.cs
- InstantRepair.cs
- LayMines.cs
- MoveToDock.cs
- Parachute.cs
- PickupUnit.cs
- RemoveSelf.cs
- RepairBridge.cs
- Resupply.cs
- RideTransport.cs
- Sell.cs
- SimpleTeleport.cs
- Transform.cs
- Turn.cs
- UnloadCargo.cs
- Wait.cs

### Activities\Air

- DeliverBulkOrder.cs
- FallToEarth.cs
- Fly.cs
- FlyAttack.cs
- FlyFollow.cs
- FlyForward.cs
- FlyIdle.cs
- FlyOffMap.cs
- Land.cs
- ReturnToBase.cs
- TakeOff.cs

### Activities\Move

- AttackMoveActivity.cs
- Drag.cs
- Follow.cs
- LocalMoveIntoTarget.cs
- Move.cs
- MoveAdjacentTo.cs
- MoveCooldownHelper.cs
- MoveOnto.cs
- MoveOntoAndTurn.cs
- MoveWithinRange.cs
- Nudge.cs

### AudioLoaders

- Mp3Loader.cs
- OggLoader.cs
- WavLoader.cs

### Commands

- ChatCommands.cs
- DebugVisualizationCommands.cs
- DevCommands.cs
- HelpCommand.cs
- PlayerCommands.cs

### EditorBrushes

- EditorActorBrush.cs
- EditorBlit.cs
- EditorCopyPasteBrush.cs
- EditorDefaultBrush.cs
- EditorMarkerLayerBrush.cs
- EditorResourceBrush.cs
- EditorTileBrush.cs
- EditorTilingPathBrush.cs

### Effects

- Beacon.cs
- ContrailFader.cs
- FlashTarget.cs
- FloatingSprite.cs
- FloatingText.cs
- MapNotificationEffect.cs
- RallyPointIndicator.cs
- RevealShroudEffect.cs
- SpawnActorEffect.cs
- SpriteAnnotation.cs
- SpriteEffect.cs

### FileFormats

- Blast.cs
- FastByteReader.cs
- ImaAdpcmReader.cs
- IniFile.cs
- InstallShieldCABCompression.cs
- MSCabCompression.cs
- RLEZerosCompression.cs
- WavReader.cs
- WestwoodCompressedReader.cs

### FileSystem

- ContentInstallerFileSystemLoader.cs
- DefaultFileSystemLoader.cs
- InstallShieldPackage.cs
- ISO9660.cs

### Graphics

- ActorPreview.cs
- BeamRenderable.cs
- BorderedRegionRenderable.cs
- CircleAnnotationRenderable.cs
- ContrailRenderable.cs
- DefaultSpriteSequence.cs
- DetectionCircleAnnotationRenderable.cs
- EditorSelectionAnnotationRenderable.cs
- IsometricSelectionBarsAnnotationRenderable.cs
- IsometricSelectionBoxAnnotationRenderable.cs
- LineAnnotationRenderable.cs
- PolygonAnnotationRenderable.cs
- RailgunRenderable.cs
- RangeCircleAnnotationRenderable.cs
- SelectionBarsAnnotationRenderable.cs
- SelectionBoxAnnotationRenderable.cs
- SpriteActorPreview.cs
- TextAnnotationRenderable.cs
- TilesetSpecificSpriteSequence.cs
- UITextRenderable.cs

### HitShapes

- Capsule.cs
- Circle.cs
- IHitShape.cs
- Polygon.cs
- Rectangle.cs

### Installer

- Availability.cs
- InstallerUtils.cs
- ISourceAction.cs
- ISourceResolver.cs

### Installer\SourceActions

- CopySourceAction.cs
- DeleteSourceAction.cs
- ExtractBlastSourceAction.cs
- ExtractIscabSourceAction.cs
- ExtractMscabSourceAction.cs
- ExtractRawSourceAction.cs
- ExtractZipSourceAction.cs

### Installer\SourceResolvers

- DiscSourceResolver.cs
- GogSourceResolver.cs
- RegistryDirectoryFromFileSourceResolver.cs
- RegistryDirectorySourceResolver.cs
- SteamSourceResolver.cs

### Lint

- CheckActorReferences.cs
- CheckActors.cs
- CheckAngle.cs
- CheckChromeHotkeys.cs
- CheckChromeIntegerExpressions.cs
- CheckChromeLogic.cs
- CheckConditions.cs
- CheckConflictingMouseBounds.cs
- CheckCursors.cs
- CheckDefaultVisibility.cs
- CheckFluentReferences.cs
- CheckFluentSyntax.cs
- CheckHitShapes.cs
- CheckInteractable.cs
- CheckLocomotorReferences.cs
- CheckLuaScript.cs
- CheckMapCordon.cs
- CheckMapMetadata.cs
- CheckMapTiles.cs
- CheckMultiBrushes.cs
- CheckNotifications.cs
- CheckOwners.cs
- CheckPalettes.cs
- CheckPlayers.cs
- CheckRangeLimit.cs
- CheckRevealFootprint.cs
- CheckRunningUpdateRule.cs
- CheckSequences.cs
- CheckSpriteBodies.cs
- CheckSyncAnnotations.cs
- CheckTooltips.cs
- CheckTraitLocation.cs
- CheckTraitPrerequisites.cs
- CheckUnknownTraitFields.cs
- CheckUnknownWeaponFields.cs
- CheckVoiceReferences.cs
- CheckWorldAndPlayerInherits.cs
- LintBuildablePrerequisites.cs
- LintExts.cs

### LoadScreens

- BlankLoadScreen.cs
- LogoStripeLoadScreen.cs
- ModContentLoadScreen.cs
- SheetLoadScreen.cs

### MapGenerator

- ActorPlan.cs
- CellLayerUtils.cs
- Direction.cs
- LatTiler.cs
- MapGeneratorSettings.cs
- Matrix.cs
- MatrixUtils.cs
- MultiBrush.cs
- NoiseUtils.cs
- RampTiler.cs
- Symmetry.cs
- Terraformer.cs
- TilingPath.cs

### Orders

- BeaconOrderGenerator.cs
- DeployOrderTargeter.cs
- EnterAlliedActorTargeter.cs
- ForceModifiersOrderGenerator.cs
- GlobalButtonOrderGenerator.cs
- GuardOrderGenerator.cs
- OrderGenerator.cs
- PlaceBuildingOrderGenerator.cs
- RepairOrderGenerator.cs
- UnitOrderGenerator.cs
- UnitOrderTargeter.cs

### Pathfinder

- CellInfo.cs
- CellInfoLayerPool.cs
- DensePathGraph.cs
- Grid.cs
- GridPathGraph.cs
- HierarchicalPathFinder.cs
- IPathGraph.cs
- MapPathGraph.cs
- PathSearch.cs
- SparsePathGraph.cs

### Projectiles

- AreaBeam.cs
- Bullet.cs
- GravityBomb.cs
- InstantHit.cs
- LaserZap.cs
- Missile.cs
- NukeLaunch.cs
- Railgun.cs

### Scripting

- CallLuaFunc.cs
- LuaScript.cs
- Media.cs
- ScriptEmmyTypeOverrideAttribute.cs
- ScriptTriggers.cs

### Scripting\Global

- ActorGlobal.cs
- AngleGlobal.cs
- BeaconGlobal.cs
- CameraGlobal.cs
- ColorGlobal.cs
- CoordinateGlobals.cs
- DateTimeGlobal.cs
- LightingGlobal.cs
- MapGlobal.cs
- MediaGlobal.cs
- PlayerGlobal.cs
- RadarGlobal.cs
- ReinforcementsGlobal.cs
- TriggerGlobal.cs
- UserInterfaceGlobal.cs
- UtilsGlobal.cs

### Scripting\Properties

- AircraftProperties.cs
- AirstrikeProperties.cs
- AmmoPoolProperties.cs
- CaptureProperties.cs
- CarryallProperties.cs
- CloakProperties.cs
- CombatProperties.cs
- ConditionProperties.cs
- DeliveryProperties.cs
- DemolitionProperties.cs
- DiplomacyProperties.cs
- GainsExperienceProperties.cs
- GeneralProperties.cs
- GuardProperties.cs
- HarvesterProperties.cs
- HealthProperties.cs
- InstantlyRepairsProperties.cs
- MissionObjectiveProperties.cs
- MobileProperties.cs
- NukeProperties.cs
- ParadropProperties.cs
- ParatroopersProperties.cs
- PlayerConditionProperties.cs
- PlayerExperienceProperties.cs
- PlayerProperties.cs
- PlayerStatsProperties.cs
- PowerProperties.cs
- ProductionProperties.cs
- RepairableBuildingProperties.cs
- ResourceProperties.cs
- ScaredCatProperties.cs
- SellableProperties.cs
- TransformProperties.cs
- TransportProperties.cs

### ServerTraits

- LobbyCommands.cs
- MasterServerPinger.cs
- PlayerPinger.cs
- SkirmishLogic.cs

### SpriteLoaders

- DdsLoader.cs
- EmbeddedSpritePalette.cs
- PngSheetLoader.cs
- ShpTSLoader.cs
- TgaLoader.cs

### Terrain

- DefaultTerrain.cs
- DefaultTileCache.cs
- TerrainInfo.cs

### Traits

- AcceptsDeliveredCash.cs
- AcceptsDeliveredExperience.cs
- ActorSpawner.cs
- AffectsShroud.cs
- AmmoPool.cs
- AppearsOnMapPreview.cs
- Armament.cs
- Armor.cs
- AttackMove.cs
- AttackWander.cs
- AutoCarryable.cs
- AutoCarryall.cs
- AutoCrusher.cs
- AutoTarget.cs
- AutoTargetPriority.cs
- BlocksProjectiles.cs
- BodyOrientation.cs
- Buildable.cs
- Capturable.cs
- CapturableProgressBar.cs
- CapturableProgressBlink.cs
- CaptureManager.cs
- CaptureProgressBar.cs
- Captures.cs
- Cargo.cs
- Carryable.cs
- CarryableHarvester.cs
- Carryall.cs
- CashTrickler.cs
- ChangesHealth.cs
- ChangesTerrain.cs
- Cloak.cs
- CombatDebugOverlay.cs
- CommandBarBlacklist.cs
- CreatesShroud.cs
- Crushable.cs
- CustomSellValue.cs
- DamagedByTerrain.cs
- DeliversCash.cs
- DeliversExperience.cs
- Demolishable.cs
- Demolition.cs
- DetectCloaked.cs
- DockClientBase.cs
- DockClientManager.cs
- DockHost.cs
- EjectOnDeath.cs
- Encyclopedia.cs
- EntersTunnels.cs
- ExitsDebugOverlay.cs
- ExperienceTrickler.cs
- ExplosionOnDamageTransition.cs
- FireProjectilesOnDeath.cs
- FireWarheads.cs
- FireWarheadsOnDeath.cs
- GainsExperience.cs
- GivesBounty.cs
- GivesCashOnCapture.cs
- GivesExperience.cs
- Guard.cs
- Guardable.cs
- Harvester.cs
- Health.cs
- HitShape.cs
- Huntable.cs
- Husk.cs
- IgnoresCloak.cs
- IgnoresDisguise.cs
- Immobile.cs
- InstantlyRepairable.cs
- InstantlyRepairs.cs
- Interactable.cs
- IsometricSelectable.cs
- JamsMissiles.cs
- KillsSelf.cs
- LintAttributes.cs
- MapEditorData.cs
- Mine.cs
- Minelayer.cs
- Mobile.cs
- MustBeDestroyed.cs
- OwnerLostAction.cs
- Parachutable.cs
- ParaDrop.cs
- Passenger.cs
- Plug.cs
- Pluggable.cs
- PowerTooltip.cs
- ProducibleWithLevel.cs
- Production.cs
- ProductionBulkAirDrop.cs
- ProductionFromMapEdge.cs
- ProductionParadrop.cs
- ProductionQueueFromSelection.cs
- ProximityCaptor.cs
- ProximityCapturable.cs
- ProximityCapturableBase.cs
- QuantizeFacingsFromSequence.cs
- Rearmable.cs
- RegionProximityCapturable.cs
- RejectsOrders.cs
- ReloadAmmoPool.cs
- Repairable.cs
- RepairableNear.cs
- RepairsBridges.cs
- RepairsUnits.cs
- Replaceable.cs
- Replacement.cs
- RequiresSpecificOwners.cs
- RevealOnDeath.cs
- RevealOnFire.cs
- RevealsMap.cs
- RevealsShroud.cs
- ScriptTags.cs
- SeedsResource.cs
- Selectable.cs
- Sellable.cs
- ShakeOnDeath.cs
- SpawnActorOnDeath.cs
- SpawnActorsOnSell.cs
- StoresPlayerResources.cs
- StoresResources.cs
- Targetable.cs
- TemporaryOwnerManager.cs
- TerrainLightSource.cs
- ThrowsParticle.cs
- Tooltip.cs
- TooltipDescription.cs
- TransformCrusherOnCrush.cs
- TransformOnCapture.cs
- Transforms.cs
- TunnelEntrance.cs
- TurnOnIdle.cs
- Turreted.cs
- UpdatesDerrickCount.cs
- Valued.cs
- Voiced.cs
- Wanders.cs

### Traits\Air

- Aircraft.cs
- AttackAircraft.cs
- AttackBomber.cs
- FallsToEarth.cs

### Traits\Attack

- AttackBase.cs
- AttackCharges.cs
- AttackFollow.cs
- AttackFrontal.cs
- AttackGarrisoned.cs
- AttackOmni.cs
- AttackTurreted.cs

### Traits\BotModules

- BaseBuilderBotModule.cs
- BuildingRepairBotModule.cs
- CaptureManagerBotModule.cs
- HarvesterBotModule.cs
- McvExpansionManagerBotModule.cs
- McvManagerBotModule.cs
- PowerDownBotManager.cs
- ResourceMapBotModule.cs
- SquadManagerBotModule.cs
- SupportPowerBotModule.cs
- UnitBuilderBotModule.cs

### Traits\BotModules\BotModuleLogic

- BaseBuilderQueueManager.cs
- MinelayerBotModule.cs
- SupportPowerDecision.cs

### Traits\BotModules\Squads

- AttackOrFleeFuzzy.cs
- Squad.cs
- StateMachine.cs

### Traits\BotModules\Squads\States

- AirStates.cs
- GroundStates.cs
- ProtectionStates.cs
- StateBase.cs

### Traits\Buildings

- ActorPreviewPlaceBuildingPreview.cs
- BaseBuilding.cs
- BaseProvider.cs
- Bridge.cs
- BridgeHut.cs
- BridgePlaceholder.cs
- Building.cs
- BuildingInfluence.cs
- BuildingUtils.cs
- Exit.cs
- FootprintPlaceBuildingPreview.cs
- FreeActor.cs
- FreeActorWithDelivery.cs
- Gate.cs
- GivesBuildableArea.cs
- GroundLevelBridge.cs
- LegacyBridgeHut.cs
- LineBuild.cs
- LineBuildNode.cs
- PlaceBuildingVariants.cs
- PrimaryBuilding.cs
- ProductionAirdrop.cs
- RallyPoint.cs
- Refinery.cs
- RepairableBuilding.cs
- RequiresBuildableArea.cs
- Reservable.cs
- SequencePlaceBuildingPreview.cs
- TransformsIntoAircraft.cs
- TransformsIntoDockClientManager.cs
- TransformsIntoEntersTunnels.cs
- TransformsIntoMobile.cs
- TransformsIntoPassenger.cs
- TransformsIntoRepairable.cs
- TransformsIntoTransforms.cs

### Traits\Conditions

- ConditionalTrait.cs
- ExternalCondition.cs
- GrantChargedConditionOnToggle.cs
- GrantCondition.cs
- GrantConditionOnAttack.cs
- GrantConditionOnBotOwner.cs
- GrantConditionOnClientDock.cs
- GrantConditionOnCombatantOwner.cs
- GrantConditionOnDamageState.cs
- GrantConditionOnDeploy.cs
- GrantConditionOnFaction.cs
- GrantConditionOnHealth.cs
- GrantConditionOnHostDock.cs
- GrantConditionOnLayer.cs
- GrantConditionOnLineBuildDirection.cs
- GrantConditionOnMinelaying.cs
- GrantConditionOnMovement.cs
- GrantConditionOnPlayerResources.cs
- GrantConditionOnPowerState.cs
- GrantConditionOnPrerequisite.cs
- GrantConditionOnProduction.cs
- GrantConditionOnSubterraneanLayer.cs
- GrantConditionOnTerrain.cs
- GrantConditionOnTileSet.cs
- GrantConditionOnTunnelLayer.cs
- GrantConditionWhileAiming.cs
- GrantExternalConditionToCrusher.cs
- GrantExternalConditionToProduced.cs
- GrantRandomCondition.cs
- LineBuildSegmentExternalCondition.cs
- PausableConditionalTrait.cs
- ProximityExternalCondition.cs
- SpreadsCondition.cs
- ToggleConditionOnOrder.cs

### Traits\Crates

- Crate.cs
- CrateAction.cs
- DuplicateUnitCrateAction.cs
- ExplodeCrateAction.cs
- GiveBaseBuilderCrateAction.cs
- GiveCashCrateAction.cs
- GiveUnitCrateAction.cs
- GrantExternalConditionCrateAction.cs
- HealActorsCrateAction.cs
- HideMapCrateAction.cs
- LevelUpCrateAction.cs
- RevealMapCrateAction.cs
- SupportPowerCrateAction.cs

### Traits\Infantry

- ScaredyCat.cs
- TakeCover.cs
- TerrainModifiesDamage.cs

### Traits\Modifiers

- FrozenUnderFog.cs
- HiddenUnderFog.cs
- HiddenUnderShroud.cs
- WithColoredOverlay.cs

### Traits\Multipliers

- CashTricklerMultiplier.cs
- CreatesShroudMultiplier.cs
- DamageMultiplier.cs
- DetectCloakedMultiplier.cs
- FirepowerMultiplier.cs
- GainsExperienceMultiplier.cs
- GivesExperienceMultiplier.cs
- HandicapDamageMultiplier.cs
- HandicapFirepowerMultiplier.cs
- HandicapProductionTimeMultiplier.cs
- InaccuracyMultiplier.cs
- PowerMultiplier.cs
- ProductionCostMultiplier.cs
- ProductionTimeMultiplier.cs
- RangeMultiplier.cs
- ReloadAmmoDelayMultiplier.cs
- ReloadDelayMultiplier.cs
- ResourceValueMultiplier.cs
- RevealsShroudMultiplier.cs
- SpeedMultiplier.cs

### Traits\PaletteEffects

- CloakPaletteEffect.cs
- FlashPostProcessEffect.cs
- MenuPostProcessEffect.cs
- RotationPaletteEffect.cs
- TintPostProcessEffect.cs

### Traits\Palettes

- ColorPickerColorShift.cs
- ColorPickerPalette.cs
- FixedColorPalette.cs
- FixedColorShift.cs
- FixedPlayerColorShift.cs
- IndexedPalette.cs
- IndexedPlayerPalette.cs
- PaletteFromEmbeddedSpritePalette.cs
- PaletteFromFile.cs
- PaletteFromGimpOrJascFile.cs
- PaletteFromGrayscale.cs
- PaletteFromPaletteWithAlpha.cs
- PaletteFromPlayerPaletteWithAlpha.cs
- PaletteFromPng.cs
- PaletteFromRGBA.cs
- PlayerColorPalette.cs
- PlayerColorShift.cs

### Traits\Player

- AllyRepair.cs
- BulkProductionQueue.cs
- ClassicParallelProductionQueue.cs
- ClassicProductionQueue.cs
- ConquestVictoryConditions.cs
- DamgeNotifier.cs
- DeveloperMode.cs
- DummyBot.cs
- EnemyWatcher.cs
- GameSaveViewportManager.cs
- GrantConditionOnPrerequisiteManager.cs
- HarvesterAttackNotifier.cs
- LobbyPrerequisiteCheckbox.cs
- MissionObjectives.cs
- ModularBot.cs
- ParallelProductionQueue.cs
- PlaceBeacon.cs
- PlaceBuilding.cs
- PlayerExperience.cs
- PlayerRadarTerrain.cs
- PlayerResources.cs
- PlayerStatistics.cs
- ProductionQueue.cs
- ProvidesPrerequisite.cs
- ProvidesTechPrerequisite.cs
- ResourceStorageWarning.cs
- StrategicVictoryConditions.cs
- TechTree.cs

### Traits\Power

- AffectedByPowerOutage.cs
- Power.cs
- ScalePowerWithHealth.cs

### Traits\Power\Player

- PowerManager.cs

### Traits\Radar

- AppearsOnRadar.cs
- ProvidesRadar.cs
- RadarColorFromTerrain.cs

### Traits\Render

- CashTricklerBar.cs
- Contrail.cs
- CustomTerrainDebugOverlay.cs
- DrawLineToTarget.cs
- FloatingSpriteEmitter.cs
- Hovers.cs
- IsometricSelectionDecorations.cs
- LeavesTrails.cs
- ProductionBar.cs
- ProductionIconOverlayManager.cs
- ReloadArmamentsBar.cs
- RenderDebugState.cs
- RenderDetectionCircle.cs
- RenderJammerCircle.cs
- RenderMouseBounds.cs
- RenderRangeCircle.cs
- RenderShroudCircle.cs
- RenderSprites.cs
- RenderSpritesEditorOnly.cs
- RenderUtils.cs
- SelectionDecorations.cs
- SelectionDecorationsBase.cs
- SupportPowerChargeBar.cs
- TimedConditionBar.cs
- WithAcceptDeliveredCashAnimation.cs
- WithAimAnimation.cs
- WithAircraftLandingEffect.cs
- WithAmmoPipsDecoration.cs
- WithAttackAnimation.cs
- WithAttackOverlay.cs
- WithBridgeSpriteBody.cs
- WithBuildingPlacedAnimation.cs
- WithBuildingPlacedOverlay.cs
- WithBuildingRepairDecoration.cs
- WithCargoPipsDecoration.cs
- WithChargeOverlay.cs
- WithChargeSpriteBody.cs
- WithCrateBody.cs
- WithDamageOverlay.cs
- WithDeadBridgeSpriteBody.cs
- WithDeathAnimation.cs
- WithDecoration.cs
- WithDecorationBase.cs
- WithDeliveryAnimation.cs
- WithDockedOverlay.cs
- WithDockingAnimation.cs
- WithDockingOverlay.cs
- WithFacingSpriteBody.cs
- WithGateSpriteBody.cs
- WithHarvestAnimation.cs
- WithHarvestOverlay.cs
- WithIdleAnimation.cs
- WithIdleOverlay.cs
- WithInfantryBody.cs
- WithMakeAnimation.cs
- WithMakeOverlay.cs
- WithMoveAnimation.cs
- WithMuzzleOverlay.cs
- WithNameTagDecoration.cs
- WithParachute.cs
- WithProductionDoorOverlay.cs
- WithProductionIconOverlay.cs
- WithProductionOverlay.cs
- WithRangeCircle.cs
- WithRepairOverlay.cs
- WithResourceLevelOverlay.cs
- WithResourceLevelSpriteBody.cs
- WithResourceStoragePipsDecoration.cs
- WithResupplyAnimation.cs
- WithShadow.cs
- WithSpriteBarrel.cs
- WithSpriteBody.cs
- WithSpriteControlGroupDecoration.cs
- WithSpriteTurret.cs
- WithStoresResourcesPipsDecoration.cs
- WithSupportPowerActivationAnimation.cs
- WithSupportPowerActivationOverlay.cs
- WithSwitchableOverlay.cs
- WithTextControlGroupDecoration.cs
- WithTextDecoration.cs
- WithTurretAimAnimation.cs
- WithTurretAttackAnimation.cs
- WithWallSpriteBody.cs

### Traits\Sound

- ActorLostNotification.cs
- AmbientSound.cs
- AnnounceOnKill.cs
- AnnounceOnSeen.cs
- AttackSounds.cs
- CaptureNotification.cs
- DeathSounds.cs
- SoundOnDamageTransition.cs
- VoiceAnnouncement.cs

### Traits\SupportPowers

- AirstrikePower.cs
- DirectionalSupportPower.cs
- GrantExternalConditionPower.cs
- NukePower.cs
- ParatroopersPower.cs
- ProduceActorPower.cs
- SelectDirectionalTarget.cs
- SpawnActorPower.cs
- SupportPower.cs
- SupportPowerManager.cs

### Traits\World

- ActorMap.cs
- ActorMapOverlay.cs
- ActorSpawnManager.cs
- AutoSave.cs
- BridgeLayer.cs
- BuildableTerrainOverlay.cs
- CameraOvalMover.cs
- CellTriggerOverlay.cs
- ClassicMapGenerator.cs
- ClearMapGenerator.cs
- CliffBackImpassabilityLayer.cs
- ColorPickerManager.cs
- ControlGroups.cs
- CrateSpawner.cs
- CreateMapPlayers.cs
- EditorActionManager.cs
- EditorActorLayer.cs
- EditorActorPreview.cs
- EditorCursorLayer.cs
- EditorResourceLayer.cs
- ElevatedBridgeLayer.cs
- ElevatedBridgePlaceholder.cs
- ExitsDebugOverlayManager.cs
- HierarchicalPathFinderOverlay.cs
- LegacyBridgeLayer.cs
- LoadWidgetAtGameStart.cs
- Locomotor.cs
- MapBuildRadius.cs
- MapCreeps.cs
- MapOptions.cs
- MapStartingLocations.cs
- MapStartingUnits.cs
- MarkerLayerOverlay.cs
- MissionData.cs
- MusicPlaylist.cs
- OrderEffects.cs
- PathFinder.cs
- PathFinderOverlay.cs
- RadarPings.cs
- RenderPostProcessPassBase.cs
- ResourceClaimLayer.cs
- ResourceLayer.cs
- ResourceRenderer.cs
- ScriptLobbyDropdown.cs
- Selection.cs
- ShroudRenderer.cs
- SmudgeLayer.cs
- SpawnMapActors.cs
- SpawnStartingUnits.cs
- StartGameNotification.cs
- SubterraneanActorLayer.cs
- SubterraneanLocomotor.cs
- TerrainGeometryOverlay.cs
- TerrainLighting.cs
- TerrainRenderer.cs
- TerrainTunnel.cs
- TerrainTunnelLayer.cs
- TilingPathTool.cs
- TimeLimitManager.cs
- ValidateOrder.cs
- WarheadDebugOverlay.cs
- WeatherOverlay.cs

### UpdateRules

- MockUpdateRule.cs
- UpdatePath.cs
- UpdateRule.cs
- UpdateUtils.cs

### UpdateRules\Rules\20230225

- AddColorPickerValueRange.cs
- ExplicitSequenceFilenames.cs
- ProductionTabsWidgetAddTabButtonCollection.cs
- RemoveExperienceFromInfiltrates.cs
- RemoveNegativeSequenceLength.cs
- RemoveSequenceHasEmbeddedPalette.cs
- RemoveTSRefinery.cs
- RenameContrailWidth.cs
- RenameEngineerRepair.cs
- RenameMcvCrateAction.cs
- TextNotificationsDisplayWidgetRemoveTime.cs

### UpdateRules\Rules\20231010

- AbstractDocking.cs
- AddMarkerLayerOverlay.cs
- AddSupportPowerBlockedCursor.cs
- ExtractResourceStorageFromHarvester.cs
- MovePreviewFacing.cs
- RemoveConyardChronoReturnAnimation.cs
- RemoveEditorSelectionLayerProperties.cs
- RemoveParentTopParentLeftSubstitutions.cs
- RemoveValidRelationsFromCapturable.cs
- RenameOnDeath.cs
- RenameWidgetSubstitutions.cs
- ReplaceCloakPalette.cs
- ReplacePaletteModifiers.cs

### UpdateRules\Rules\20250330

- EditorMarkerTileLabels.cs
- RemoveAlwaysVisible.cs
- RemoveAndRenameDefenseRadiusInBaseBuilderBotModule.cs
- RemoveBarracksTypesAndVehiclesTypesInBaseBuilderBotModule.cs
- RemoveBuildingInfoAllowPlacementOnResources.cs
- ReplaceBaseAttackNotitifer.cs
- WithDamageOverlayPropertyRename.cs

### UtilityCommands

- CheckConditionalTraitInterfaceOverrides.cs
- CheckExplicitInterfacesCommand.cs
- CheckMissingSprites.cs
- CheckYaml.cs
- ConvertSpriteToPngCommand.cs
- CreateManPage.cs
- DebugChromeRegions.cs
- DumpSequenceSheetsCommand.cs
- ExtractChromeStrings.cs
- ExtractFilesCommand.cs
- ExtractMapRules.cs
- ExtractYamlStrings.cs
- FuzzMapGeneratorCommand.cs
- GetMapHashCommand.cs
- LintInterfaces.cs
- ListInstallShieldCabContentsCommand.cs
- ListMSCabContentsCommand.cs
- MapCommand.cs
- OutputResolvedRulesCommand.cs
- OutputResolvedSequencesCommand.cs
- OutputResolvedWeaponsCommand.cs
- PngSheetExportMetadataCommand.cs
- PngSheetImportMetadataCommand.cs
- ReplayMetadataCommand.cs
- ResizeMapCommand.cs
- Rgba2Hex.cs
- UpdateMapCommand.cs
- UpdateModCommand.cs
- UtilityHelpers.cs

### UtilityCommands\Documentation

- DocumentationHelpers.cs
- ExtractEmmyLuaAPI.cs
- ExtractLuaDocsCommand.cs
- ExtractSettingsDocsCommand.cs
- ExtractSpriteSequenceDocsCommand.cs
- ExtractTraitDocsCommand.cs
- ExtractWeaponDocsCommand.cs
- ExtractZeroBraneStudioLuaAPI.cs

### UtilityCommands\Documentation\Objects

- ExtractedClassFieldAttributeInfo.cs
- ExtractedClassFieldInfo.cs
- ExtractedClassInfo.cs
- ExtractedEnumInfo.cs
- ExtractedTraitInfo.cs

### Warheads

- ChangeOwnerWarhead.cs
- CreateEffectWarhead.cs
- CreateResourceWarhead.cs
- DamageWarhead.cs
- DestroyResourceWarhead.cs
- FireClusterWarhead.cs
- FlashEffectWarhead.cs
- FlashTargetsInRadiusWarhead.cs
- GrantExternalConditionWarhead.cs
- HealthPercentageDamageWarhead.cs
- LeaveSmudgeWarhead.cs
- ShakeScreenWarhead.cs
- SpreadDamageWarhead.cs
- TargetDamageWarhead.cs
- Warhead.cs

### Widgets

- ActorPreviewWidget.cs
- BackgroundWidget.cs
- BadgeWidget.cs
- ButtonWidget.cs
- CheckboxWidget.cs
- ClientTooltipRegionWidget.cs
- ColorBlockWidget.cs
- ColorMixerWidget.cs
- ConfirmationDialogs.cs
- ControlGroupsWidget.cs
- DropDownButtonWidget.cs
- EditorViewportControllerWidget.cs
- ExponentialSliderWidget.cs
- GeneratedMapPreviewWidget.cs
- GradientColorBlockWidget.cs
- GridLayout.cs
- HotkeyEntryWidget.cs
- HueSliderWidget.cs
- ImageWidget.cs
- LabelForInputWidget.cs
- LabelWidget.cs
- LabelWithHighlightWidget.cs
- LabelWithTooltipWidget.cs
- LineGraphWidget.cs
- ListLayout.cs
- LogicKeyListenerWidget.cs
- LogicTickerWidget.cs
- MapPreviewWidget.cs
- MenuButtonWidget.cs
- MouseAttachmentWidget.cs
- ObserverArmyIconsWidget.cs
- ObserverProductionIconsWidget.cs
- ObserverSupportPowerIconsWidget.cs
- PasswordFieldWidget.cs
- PerfGraphWidget.cs
- ProductionPaletteWidget.cs
- ProductionTabsWidget.cs
- ProductionTypeButtonWidget.cs
- ProgressBarWidget.cs
- RadarWidget.cs
- ResourceBarWidget.cs
- ResourcePreviewWidget.cs
- RGBASpriteWidget.cs
- ScrollableLineGraphWidget.cs
- ScrollItemWidget.cs
- ScrollPanelWidget.cs
- SelectionUtils.cs
- SliderWidget.cs
- SpriteWidget.cs
- StrategicProgressWidget.cs
- SupportPowersWidget.cs
- SupportPowerTimerWidget.cs
- TerrainTemplatePreviewWidget.cs
- TextFieldWidget.cs
- TextNotificationsDisplayWidget.cs
- TooltipContainerWidget.cs
- VideoPlayerWidget.cs
- ViewportControllerWidget.cs
- WidgetUtils.cs
- WorldButtonWidget.cs
- WorldInteractionControllerWidget.cs
- WorldLabelWithTooltipWidget.cs

### Widgets\Logic

- AnonymousProfileTooltipLogic.cs
- AssetBrowserLogic.cs
- BotTooltipLogic.cs
- ButtonTooltipLogic.cs
- ColorPickerLogic.cs
- CommandHistory.cs
- ConnectionLogic.cs
- CreditsLogic.cs
- DepthPreviewHotkeysLogic.cs
- DirectConnectLogic.cs
- DisconnectWatcherLogic.cs
- EncyclopediaLogic.cs
- GameSaveBrowserLogic.cs
- GameSaveUtils.cs
- IntroductionPromptLogic.cs
- LoadGameBrowserLogic.cs
- LoadLocalPlayerProfileLogic.cs
- LocalProfileLogic.cs
- MainMenuLogic.cs
- MapChooserLogic.cs
- MapGeneratorLogic.cs
- MissionBrowserLogic.cs
- MultiplayerLogic.cs
- MusicHotkeyLogic.cs
- MusicPlayerLogic.cs
- MuteHotkeyLogic.cs
- MuteIndicatorLogic.cs
- PerfDebugLogic.cs
- PlayerProfileBadgesLogic.cs
- RegisteredProfileTooltipLogic.cs
- ReplayBrowserLogic.cs
- ReplayUtils.cs
- ScreenshotHotkeyLogic.cs
- ServerCreationLogic.cs
- ServerListLogic.cs
- SimpleTooltipLogic.cs
- SingleHotkeyBaseLogic.cs
- SystemInfoPromptLogic.cs
- TabCompletionLogic.cs
- VersionLabelLogic.cs

### Widgets\Logic\Editor

- ActorEditLogic.cs
- ActorSelectorLogic.cs
- CommonSelectorLogic.cs
- HistoryLogLogic.cs
- LayerSelectorLogic.cs
- MapEditorLogic.cs
- MapEditorSelectionLogic.cs
- MapEditorTabsLogic.cs
- MapGeneratorToolLogic.cs
- MapMarkerTilesLogic.cs
- MapOverlaysLogic.cs
- MapToolsLogic.cs
- NewMapLogic.cs
- SaveMapLogic.cs
- TileSelectorLogic.cs
- TilingPathToolLogic.cs

### Widgets\Logic\Ingame

- AddFactionSuffixLogic.cs
- ArmyTooltipLogic.cs
- ClassicProductionLogic.cs
- CommandBarLogic.cs
- DebugLogic.cs
- DebugMenuLogic.cs
- GameInfoBriefingLogic.cs
- GameInfoLogic.cs
- GameInfoObjectivesLogic.cs
- GameInfoStatsLogic.cs
- GameSaveLoadingLogic.cs
- GameTimerLogic.cs
- HierarchicalPathFinderOverlayLogic.cs
- IngameCashCounterLogic.cs
- IngameChatLogic.cs
- IngameMenuLogic.cs
- IngamePowerBarLogic.cs
- IngamePowerCounterLogic.cs
- IngameRadarDisplayLogic.cs
- IngameSiloBarLogic.cs
- IngameTransientNotificationsLogic.cs
- LoadIngameChatLogic.cs
- LoadIngameHierarchicalPathFinderOverlayLogic.cs
- LoadIngamePerfLogic.cs
- LoadIngamePlayerOrObserverUILogic.cs
- LoadMapEditorLogic.cs
- MenuButtonsChromeLogic.cs
- ObserverShroudSelectorLogic.cs
- ObserverStatsLogic.cs
- OrderButtonsChromeLogic.cs
- ProductionTabsLogic.cs
- ProductionTooltipLogic.cs
- ReplayControlBarLogic.cs
- ScriptErrorLogic.cs
- StanceSelectorLogic.cs
- SupportPowerBinLogic.cs
- SupportPowerTooltipLogic.cs
- WorldTooltipLogic.cs

### Widgets\Logic\Ingame\Hotkeys

- CycleBasesHotkeyLogic.cs
- CycleHarvestersHotkeyLogic.cs
- CycleProductionActorsHotkeyLogic.cs
- CycleStatusBarsHotkeyLogic.cs
- DisableAllUIKeyLogic.cs
- DisableUIKeyLogic.cs
- EditorQuickSaveHotkeyLogic.cs
- JumpToLastEventHotkeyLogic.cs
- JumpToSelectedActorsHotkeyLogic.cs
- PauseHotkeyLogic.cs
- RemoveFromControlGroupHotkeyLogic.cs
- ResetZoomHotkey.cs
- SelectAllUnitsHotkeyLogic.cs
- SelectUnitsByTypeHotkeyLogic.cs
- TogglePlayerStanceColorHotkeyLogic.cs

### Widgets\Logic\Installation

- DownloadPackageLogic.cs
- InstallFromSourceLogic.cs
- ModContentLogic.cs
- ModContentPromptLogic.cs
- ModContentSourceTooltipLogic.cs

### Widgets\Logic\Lobby

- KickClientLogic.cs
- KickSpectatorsLogic.cs
- LatencyTooltipLogic.cs
- LobbyLogic.cs
- LobbyOptionsLogic.cs
- LobbyUtils.cs
- MapPreviewLogic.cs
- SpawnSelectorTooltipLogic.cs

### Widgets\Logic\Settings

- AdvancedSettingsLogic.cs
- AudioSettingsLogic.cs
- DisplaySettingsLogic.cs
- GamePlaySettingsLogic.cs
- HotkeysSettingsLogic.cs
- InputSettingsLogic.cs
- SettingsLogic.cs
- SettingsUtils.cs

## OpenRA.Mods.Cnc (140 files)

### 

- CncLoadScreen.cs
- TraitsInterfaces.cs
- Util.cs

### Activities

- Infiltrate.cs
- Leap.cs
- LeapAttack.cs
- Teleport.cs

### AudioLoaders

- AudLoader.cs
- VocLoader.cs

### Effects

- ConyardChronoVortex.cs
- GpsDotEffect.cs
- GpsSatellite.cs
- SatelliteLaunch.cs

### FileFormats

- AudReader.cs
- Blowfish.cs
- BlowfishKeyProvider.cs
- HvaReader.cs
- IdxEntry.cs
- IdxReader.cs
- LCWCompression.cs
- LZOCompression.cs
- VqaVideo.cs
- VxlReader.cs
- WsaVideo.cs
- XccGlobalDatabase.cs
- XccLocalDatabase.cs
- XORDeltaCompression.cs

### FileSystem

- BigFile.cs
- MegFile.cs
- MixFile.cs
- PackageEntry.cs
- Pak.cs

### Graphics

- ChronoVortexRenderable.cs
- ClassicSpriteSequence.cs
- ClassicTilesetSpecificSpriteSequence.cs
- ModelActorPreview.cs
- ModelRenderable.cs
- TeslaZapRenderable.cs
- UIModelRenderable.cs
- Voxel.cs
- VoxelLoader.cs

### Installer

- ExtractMixSourceAction.cs

### Projectiles

- DropPodImpact.cs
- IonCannon.cs
- TeslaZap.cs

### Scripting\Properties

- ChronosphereProperties.cs
- DisguiseProperties.cs
- InfiltrateProperties.cs
- IonCannonProperties.cs

### SpriteLoaders

- ShpD2Loader.cs
- ShpRemasteredLoader.cs
- ShpTDLoader.cs
- TmpRALoader.cs
- TmpTDLoader.cs
- TmpTSLoader.cs

### Traits

- Chronoshiftable.cs
- ClassicFacingBodyOrientation.cs
- Cloneable.cs
- ConyardChronoReturn.cs
- Disguise.cs
- DrainPrerequisitePowerOnDamage.cs
- EdibleByLeap.cs
- EnergyWall.cs
- FrozenUnderFogUpdatedByGps.cs
- GpsDot.cs
- GpsWatcher.cs
- HarvesterHuskModifier.cs
- MadTank.cs
- PortableChrono.cs
- ResourcePurifier.cs
- TDGunboat.cs
- TransferTimedExternalConditionOnTransform.cs
- TransformsNearResources.cs

### Traits\Attack

- AttackLeap.cs
- AttackPopupTurreted.cs
- AttackTDGunboatTurreted.cs
- AttackTesla.cs

### Traits\Buildings

- ClonesProducedUnits.cs

### Traits\Conditions

- GrantConditionOnJumpjetLayer.cs

### Traits\Infiltration

- InfiltrateForCash.cs
- InfiltrateForDecoration.cs
- InfiltrateForExploration.cs
- InfiltrateForPowerOutage.cs
- InfiltrateForSupportPower.cs
- InfiltrateForSupportPowerReset.cs
- InfiltrateForTransform.cs
- Infiltrates.cs

### Traits\PaletteEffects

- ChronoshiftPostProcessEffect.cs
- LightPaletteRotator.cs

### Traits\Render

- RenderVoxels.cs
- WithBuildingBib.cs
- WithCargo.cs
- WithDisguisingInfantryBody.cs
- WithEmbeddedTurretSpriteBody.cs
- WithGunboatBody.cs
- WithHarvesterSpriteBody.cs
- WithLandingCraftAnimation.cs
- WithSplitAttackPaletteInfantryBody.cs
- WithTeslaChargeAnimation.cs
- WithTeslaChargeOverlay.cs
- WithVoxelBarrel.cs
- WithVoxelBody.cs
- WithVoxelTurret.cs
- WithVoxelUnloadBody.cs
- WithVoxelWalkerBody.cs

### Traits\SupportPowers

- AttackOrderPower.cs
- ChronoshiftPower.cs
- DropPodsPower.cs
- GpsPower.cs
- GrantPrerequisiteChargeDrainPower.cs
- IonCannonPower.cs

### Traits\World

- ChronoVortexRenderer.cs
- JumpjetActorLayer.cs
- JumpjetLocomotor.cs
- ModelRenderer.cs
- ShroudPalette.cs
- TSEditorResourceLayer.cs
- TSMapGenerator.cs
- TSResourceLayer.cs
- TSShroudPalette.cs
- TSTiberiumRenderer.cs
- TSVeinsRenderer.cs
- VoxelCache.cs
- VoxelNormalsPalette.cs
- WithResourceAnimation.cs

### UtilityCommands

- ConvertPngToShpCommand.cs
- Glob.cs
- ImportGen1MapCommand.cs
- ImportGen2MapCommand.cs
- ImportRedAlertMapCommand.cs
- ImportTiberianDawnMapCommand.cs
- ImportTiberianSunMapCommand.cs
- LegacyRulesImporter.cs
- LegacySequenceImporter.cs
- LegacyTilesetImporter.cs
- RemapShpCommand.cs

### VideoLoaders

- VqaLoader.cs
- WsaLoader.cs

### Widgets

- ModelWidget.cs

### Widgets\Logic

- PreReleaseWarningPrompt.cs

## OpenRA.Mods.D2k (23 files)

### Activities

- SwallowActor.cs

### Graphics

- D2kSpriteSequence.cs
- SonicBlastRenderable.cs

### PackageLoaders

- D2kSoundResources.cs

### Projectiles

- SonicBlast.cs

### SpriteLoaders

- R8Loader.cs

### Traits

- AttackSwallow.cs
- AttractsWorms.cs
- Sandworm.cs
- SpiceBloom.cs

### Traits\Buildings

- D2kActorPreviewPlaceBuildingPreview.cs
- D2kBuilding.cs

### Traits\Player

- HarvesterInsurance.cs

### Traits\Render

- WithCrumbleOverlay.cs
- WithDeliveryOverlay.cs

### Traits\World

- BuildableTerrainLayer.cs
- D2kMapGenerator.cs
- D2kResourceRenderer.cs
- SonicBlastRenderer.cs

### UtilityCommands

- D2kMapImporter.cs
- ImportD2kMapCommand.cs

### Warheads

- DamagesConcreteWarhead.cs

### Widgets\Logic

- PurchaseWidgetLogic.cs

## OpenRA.Platforms.Default (18 files)

### 

- DefaultPlatform.cs
- DummySoundEngine.cs
- FrameBuffer.cs
- FreeTypeFont.cs
- ITextureInternal.cs
- MultiTapDetection.cs
- OpenAlSoundEngine.cs
- OpenGL.cs
- Sdl2GraphicsContext.cs
- Sdl2HardwareCursor.cs
- Sdl2Input.cs
- Sdl2PlatformWindow.cs
- Shader.cs
- StaticIndexBuffer.cs
- Texture.cs
- ThreadAffine.cs
- ThreadedGraphicsContext.cs
- VertexBuffer.cs

## OpenRA.Server (1 files)

### 

- Program.cs

## OpenRA.Utility (1 files)

### 

- Program.cs

## OpenRA.Launcher (1 files)

### 

- Program.cs

## OpenRA.WindowsLauncher (1 files)

### 

- Program.cs

## OpenRA.Test (20 files)

### OpenRA.Game

- ActionQueueTest.cs
- ActorInfoTest.cs
- CoordinateTest.cs
- CPosTest.cs
- FieldLoaderTest.cs
- FieldSaverTest.cs
- FluentTest.cs
- MediatorTest.cs
- MiniYamlTest.cs
- OrderTest.cs
- PlatformTest.cs
- PngTest.cs
- PriorityArrayTest.cs
- PriorityQueueTest.cs
- Sha1Tests.cs
- SpatiallyPartitionedTest.cs
- StreamExtsTests.cs
- VariableExpressionTest.cs

### OpenRA.Mods.Common

- PerfGraphWidgetTest.cs
- ShapeTest.cs

