package com.example.villagertracker;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.minecraft.entity.passive.EntityVillager;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.AxisAlignedBB;
import net.minecraft.world.WorldServer;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.FMLCommonHandler;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.event.FMLInitializationEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.gameevent.TickEvent;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Mod(modid = Villagertracker.MODID, name = "Villager Tracker", version = "1.0")
public class Villagertracker {
    public static final String MODID = "villagertracker";
    private static final String OUTPUT_FILE = "villager_positions.json";

    public Villagertracker() {
        System.out.println("[VillagerTracker] Mod has been initialized.");
        MinecraftForge.EVENT_BUS.register(this);
    }

    @Mod.EventHandler
    public void init(FMLInitializationEvent event) {
    }

    @SubscribeEvent
    public void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase == TickEvent.Phase.END) {
            MinecraftServer server = FMLCommonHandler.instance().getMinecraftServerInstance();
            if (server != null) {
                WorldServer world = server.worldServerForDimension(0);
                if (world != null) {
                    List<EntityPlayerMP> players = server.getPlayerList().getPlayers();
                    if (!players.isEmpty()) {
                        EntityPlayerMP player = players.get(0);

                        double range = 50.0;
                        AxisAlignedBB aabb = new AxisAlignedBB(
                                player.posX - range, player.posY - range, player.posZ - range,
                                player.posX + range, player.posY + range, player.posZ + range
                        );

                        List<EntityVillager> villagers = world.getEntitiesWithinAABB(EntityVillager.class, aabb);
                        System.out.println("Found " + villagers.size() + " villagers near the player");

                        List<VillagerInfo> villagerInfos = new ArrayList<VillagerInfo>();
                        for (EntityVillager villager : villagers) {
                            String rawName = villager.getDisplayName().getUnformattedText();
                            String name;
                            if (!rawName.matches("\\A\\p{ASCII}*\\z") || rawName.equals("entity.Villager.name") || rawName.trim().isEmpty()) {
                                int prof = villager.getProfession();
                                switch (prof) {
                                    case 0:
                                        name = "Farmer";
                                        break;
                                    case 1:
                                        name = "Librarian";
                                        break;
                                    case 2:
                                        name = "Priest";
                                        break;
                                    case 3:
                                        name = "Smith";
                                        break;
                                    case 4:
                                        name = "Butcher";
                                        break;
                                    default:
                                        name = "Villager";
                                        break;
                                }
                            } else {
                                name = rawName;
                            }
                            villagerInfos.add(new VillagerInfo(
                                    name,
                                    villager.posX,
                                    villager.posY,
                                    villager.posZ
                            ));
                        }
                        writeVillagerPositions(villagerInfos);
                    } else {
                        System.out.println("No players found");
                    }
                }
            }
        }
    }

    private void writeVillagerPositions(List<VillagerInfo> villagerInfos) {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(villagerInfos);
        FileWriter writer = null;
        try {
            writer = new FileWriter(OUTPUT_FILE);
            writer.write(json);
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (writer != null) {
                try {
                    writer.close();
                } catch (IOException ex) {
                    ex.printStackTrace();
                }
            }
        }
    }

    public static class VillagerInfo {
        public String name;
        public double x;
        public double y;
        public double z;

        public VillagerInfo(String name, double x, double y, double z) {
            this.name = name;
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }
}
