
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_8fd4d59a9770e779227c048a9ad79f4d = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_9ef139b72244a6c360b6f6a96142d508 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.vault_transfer", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["background"] : "#BF5AF2", ["color"] : "#fff", ["fontSize"] : "12px", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["opacity"] : "0.85" }) }),onClick:on_click_9ef139b72244a6c360b6f6a96142d508},children)
    )
});
